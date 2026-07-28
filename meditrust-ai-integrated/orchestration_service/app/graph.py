from __future__ import annotations

import time

from orchestration_service.app.classification import classify_deterministically
from orchestration_service.app.config import Settings
from orchestration_service.app.governance_client import GovernanceServiceClient, knowledge_citation_to_governance
from orchestration_service.app.headroom import HeadroomAdapter, estimate_tokens
from orchestration_service.app.knowledge_client import (
    KnowledgeServiceClient,
    extract_citations,
    extract_document_ids,
    retrieved_chunks_to_snippets,
)
from orchestration_service.app.models import (
    ClassificationResult,
    GraphDecision,
    GraphState,
    IntentType,
    InvocationMode,
    InvocationResponse,
    PromptVersion,
    ProviderResponse,
    RiskLevel,
    TraceEvent,
)
from orchestration_service.app.prompts import get_prompt
from orchestration_service.app.providers import BaseProvider


def trace(state: GraphState, node: str, event_type: str, message: str, **details: object) -> None:
    state.trace.append(
        TraceEvent(
            node=node,
            event_type=event_type,
            message=message,
            details=dict(details),
        )
    )


class OrchestrationEngine:
    def __init__(self, settings: Settings, provider: BaseProvider):
        self.settings = settings
        self.provider = provider
        self.headroom = HeadroomAdapter(settings)
        self.knowledge = KnowledgeServiceClient(settings)
        self.governance = GovernanceServiceClient(settings)

    def run(self, request, mode: InvocationMode) -> InvocationResponse:
        start = time.perf_counter()
        prompt_version = (
            PromptVersion.baseline_v1 if mode == InvocationMode.baseline else PromptVersion.optimized_v1
        )
        state = GraphState(request=request, mode=mode, prompt_version=prompt_version)

        trace(state, "start", "entered", "Invocation started", mode=mode.value)
        self._emit_analytics(state, "meditrust_workflow_started", {"mode": mode.value})
        self._run_input_guard(state)
        if state.input_guard_decision in {"block", "escalate"}:
            return self._build_input_guard_stop_response(state, start)
        self._classify(state)
        self._hydrate_knowledge(state)

        if state.cache_hit:
            trace(state, "cache_lookup", "completed", "Using validated cache hit")
            state.provider_response = ProviderResponse(
                answer=state.cache_answer or "",
                source_ids=[citation.get("chunk_id", "") for citation in state.cache_citations],
                raw={"provider": "knowledge_cache"},
            )
            state.decision = GraphDecision(
                should_escalate=False,
                should_regenerate=False,
                final_status="completed_from_cache",
                rationale="Validated semantic cache hit.",
            )
            self._emit_analytics(state, "meditrust_cache_hit", {"request_id": request.request_id})
            state.metrics.latency_ms = int((time.perf_counter() - start) * 1000)
            trace(state, "finish", "completed", "Invocation completed", final_status=state.decision.final_status)
            response = state.provider_response
            return InvocationResponse(
                request_id=request.request_id,
                mode=state.mode,
                prompt_version=state.prompt_version,
                answer=response.answer,
                classification=state.classification
                or ClassificationResult(intent=IntentType.unknown, risk=RiskLevel.medium),
                source_ids=response.source_ids,
                citations=state.cache_citations,
                evidence_status=state.evidence_status,
                cache_hit=True,
                warnings=[],
                negative_statements=[],
                escalation_text=None,
                metrics=state.metrics,
                trace=state.trace,
                final_status=state.decision.final_status,
            )

        if state.evidence_status == "insufficient":
            trace(state, "safe_fallback", "completed", "Insufficient evidence; skipping provider generation")
            self._emit_analytics(
                state,
                "meditrust_fallback_activated",
                {"reason": "insufficient_evidence", "request_id": request.request_id},
            )
            state.provider_response = ProviderResponse(
                answer=(
                    "I could not find sufficient approved evidence to answer this safely. "
                    "Please consult an authorized clinical or compliance reviewer."
                ),
                warnings=["Insufficient evidence returned by knowledge service."],
                negative_statements=["No unsupported medical guidance was generated."],
                escalation_text="Escalate to human review.",
                source_ids=[],
                raw={"provider": "safe_fallback"},
            )
            state.decision = GraphDecision(
                should_escalate=True,
                should_regenerate=False,
                final_status="insufficient_evidence",
                rationale="Knowledge service reported insufficient evidence.",
            )
            state.metrics.latency_ms = int((time.perf_counter() - start) * 1000)
            trace(state, "finish", "completed", "Invocation completed", final_status=state.decision.final_status)
            response = state.provider_response
            return InvocationResponse(
                request_id=request.request_id,
                mode=state.mode,
                prompt_version=state.prompt_version,
                answer=response.answer,
                classification=state.classification
                or ClassificationResult(intent=IntentType.unknown, risk=RiskLevel.medium),
                source_ids=response.source_ids,
                citations=[],
                evidence_status=state.evidence_status,
                cache_hit=False,
                warnings=response.warnings,
                negative_statements=response.negative_statements,
                escalation_text=response.escalation_text,
                metrics=state.metrics,
                trace=state.trace,
                final_status=state.decision.final_status,
            )

        if mode == InvocationMode.optimized:
            self._optimize_context(state)
        else:
            token_count = estimate_tokens("\n".join(item.content for item in request.source_snippets))
            state.metrics.token_count_before = token_count
            state.metrics.token_count_after = token_count

        self._generate(state)
        self._run_output_guard(state)
        self._decide(state)

        if state.decision.should_regenerate and state.regeneration_count < self.settings.max_regenerations:
            self._regenerate_once(state)

        self._write_cache_if_allowed(state)
        state.metrics.latency_ms = int((time.perf_counter() - start) * 1000)
        trace(state, "finish", "completed", "Invocation completed", final_status=state.decision.final_status)

        response = state.provider_response or ProviderResponse(answer="No provider response generated.")
        return InvocationResponse(
            request_id=request.request_id,
            mode=state.mode,
            prompt_version=state.prompt_version,
            answer=response.answer,
            classification=state.classification
            or ClassificationResult(intent=IntentType.unknown, risk=RiskLevel.medium),
            source_ids=response.source_ids,
            citations=state.retrieved_citations,
            evidence_status=state.evidence_status,
            cache_hit=state.cache_hit,
            warnings=(state.optimized_context.warnings if state.optimized_context else []) + response.warnings,
            negative_statements=(state.optimized_context.negative_statements if state.optimized_context else [])
            + response.negative_statements,
            escalation_text=response.escalation_text
            or (state.optimized_context.escalation_text if state.optimized_context else None),
            metrics=state.metrics,
            trace=state.trace,
            final_status=state.decision.final_status,
        )

    def _build_input_guard_stop_response(self, state: GraphState, start: float) -> InvocationResponse:
        decision = state.input_guard_decision or "block"
        answer = (
            "This request requires human review before the system can continue."
            if decision == "escalate"
            else "This request cannot be processed safely."
        )
        escalation_text = "Escalate to a qualified clinical or compliance reviewer." if decision == "escalate" else None
        warnings = [state.input_guard_reason] if state.input_guard_reason else []
        state.provider_response = ProviderResponse(
            answer=answer,
            warnings=warnings,
            negative_statements=["No retrieval or model generation was performed."],
            escalation_text=escalation_text,
            source_ids=[],
            raw={"provider": "input_guard"},
        )
        state.decision = GraphDecision(
            should_escalate=decision == "escalate",
            should_regenerate=False,
            final_status="blocked_by_input_guard" if decision == "block" else "escalated_by_input_guard",
            rationale="Governance input guard stopped downstream processing.",
        )
        self._emit_analytics(
            state,
            "meditrust_escalation_triggered" if decision == "escalate" else "meditrust_fallback_activated",
            {"stage": "input_guard", "decision": decision},
        )
        state.metrics.latency_ms = int((time.perf_counter() - start) * 1000)
        trace(state, "finish", "completed", "Invocation completed", final_status=state.decision.final_status)
        response = state.provider_response
        return InvocationResponse(
            request_id=state.request.request_id,
            mode=state.mode,
            prompt_version=state.prompt_version,
            answer=response.answer,
            classification=state.classification or ClassificationResult(intent=IntentType.unknown, risk=RiskLevel.medium),
            source_ids=[],
            citations=[],
            evidence_status=state.evidence_status,
            cache_hit=False,
            warnings=response.warnings,
            negative_statements=response.negative_statements,
            escalation_text=response.escalation_text,
            metrics=state.metrics,
            trace=state.trace,
            final_status=state.decision.final_status,
        )

    def _hydrate_knowledge(self, state: GraphState) -> None:
        query = state.request.query
        role = state.request.user_role
        status = state.request.status_filter
        trace(state, "cache_lookup", "entered", "Checking semantic cache")
        try:
            cache_payload = self.knowledge.cache_lookup(query=query, role=role, status=status)
            state.cache_hit = bool(cache_payload.get("cache_hit", False))
            state.cache_answer = cache_payload.get("answer")
            state.cache_citations = list(cache_payload.get("citations", []))
            if state.cache_hit:
                self._emit_analytics(state, "meditrust_cache_hit", {"similarity": cache_payload.get("similarity")})
                trace(
                    state,
                    "cache_lookup",
                    "completed",
                    "Knowledge cache hit",
                    similarity=cache_payload.get("similarity"),
                )
                return
            self._emit_analytics(state, "meditrust_cache_miss", {"request_id": state.request.request_id})
            trace(state, "cache_lookup", "completed", "Knowledge cache miss")
        except Exception as exc:  # noqa: BLE001
            trace(state, "cache_lookup", "failed", "Knowledge cache lookup failed", error=str(exc))

        trace(state, "retrieve", "entered", "Retrieving evidence from knowledge service")
        retrieval = self.knowledge.retrieve(
            query=query,
            role=role,
            top_k=state.request.top_k,
            status=status,
            source_type=state.request.source_type,
            document_ids=state.request.document_ids,
            tags=state.request.tags,
        )
        state.evidence_status = str(retrieval.get("evidence_status", "insufficient"))
        state.leakage_detected = bool(retrieval.get("leakage_detected", False))
        results = list(retrieval.get("results", []))
        state.request.source_snippets = retrieved_chunks_to_snippets(results)
        state.retrieved_document_ids = extract_document_ids(results)
        state.retrieved_citations = extract_citations(results)
        self._emit_analytics(
            state,
            "meditrust_retrieval_completed",
            {
                "results_count": len(results),
                "evidence_status": state.evidence_status,
                "leakage_detected": state.leakage_detected,
            },
        )
        trace(
            state,
            "retrieve",
            "completed",
            "Knowledge retrieval completed",
            results=len(state.request.source_snippets),
            evidence_status=state.evidence_status,
            leakage_detected=state.leakage_detected,
        )

    def _classify(self, state: GraphState) -> None:
        trace(state, "classify", "entered", "Running deterministic classification")
        result = classify_deterministically(state.request.query, self.settings.ambiguous_threshold)
        if result.ambiguous:
            trace(state, "classify", "fallback", "Ambiguous result detected; consulting provider classifier")
            provider_result = self.provider.classify_ambiguous(state.request.query)
            if not provider_result.ambiguous:
                result = provider_result
        state.classification = result
        trace(
            state,
            "classify",
            "completed",
            "Classification completed",
            intent=result.intent.value,
            risk=result.risk.value,
            ambiguous=result.ambiguous,
            used_gemini=result.used_gemini,
        )

    def _optimize_context(self, state: GraphState) -> None:
        trace(state, "optimize_context", "entered", "Optimizing retrieval context")
        optimized = self.headroom.optimize(state.request.source_snippets, state.classification)  # type: ignore[arg-type]
        state.optimized_context = optimized
        state.metrics.token_count_before = optimized.token_count_before
        state.metrics.token_count_after = optimized.token_count_after
        self._emit_analytics(
            state,
            "meditrust_context_optimized",
            {
                "method": optimized.strategy,
                "headroom_used": optimized.headroom_used,
            },
            token_metrics={
                "tokens_before_optimization": optimized.token_count_before,
                "tokens_after_optimization": optimized.token_count_after,
                "tokens_saved": max(0, optimized.token_count_before - optimized.token_count_after),
                "optimization_method": "headroom" if optimized.headroom_used else "deterministic",
            },
        )
        trace(
            state,
            "optimize_context",
            "completed",
            "Context optimization completed",
            strategy=optimized.strategy,
            headroom_used=optimized.headroom_used,
            token_count_before=optimized.token_count_before,
            token_count_after=optimized.token_count_after,
        )

    def _generate(self, state: GraphState) -> None:
        trace(state, "generate", "entered", "Generating provider response")
        prompt = get_prompt(state.prompt_version)
        snippets = state.request.source_snippets
        if state.optimized_context:
            snippets = state.optimized_context.snippets
        provider_start = time.perf_counter()
        response = self.provider.generate(prompt, state.request.query, snippets, state.classification)  # type: ignore[arg-type]
        state.metrics.provider_latency_ms += int((time.perf_counter() - provider_start) * 1000)
        state.metrics.model_invocation_count += 1
        state.provider_response = response
        self._emit_analytics(
            state,
            "meditrust_llm_invoked",
            {
                "request_id": state.request.request_id,
                "model_provider": self.settings.model_provider,
                "prompt_version": state.prompt_version.value,
            },
            token_metrics={
                "tokens_before_optimization": state.metrics.token_count_before,
                "tokens_after_optimization": state.metrics.token_count_after,
                "tokens_saved": max(0, state.metrics.token_count_before - state.metrics.token_count_after),
                "optimization_method": "headroom"
                if state.optimized_context and state.optimized_context.headroom_used
                else "deterministic"
                if state.optimized_context
                else "none",
            },
            latency_metrics={
                "total_latency_ms": state.metrics.latency_ms,
                "guard_latency_ms": 0,
                "retrieval_latency_ms": 0,
                "llm_latency_ms": state.metrics.provider_latency_ms,
                "cache_latency_ms": 0,
            },
        )
        trace(
            state,
            "generate",
            "completed",
            "Provider response generated",
            source_count=len(response.source_ids),
            warnings=len(response.warnings),
        )

    def _run_input_guard(self, state: GraphState) -> None:
        trace(state, "input_guard", "entered", "Calling governance input guard")
        payload = self.governance.input_guard(
            request_id=state.request.request_id,
            query=state.request.query,
            user_role=state.request.user_role,
            session_id=state.request.session_id,
            metadata=state.request.metadata,
        )
        state.input_guard_decision = str(payload.get("decision", "allow"))
        state.input_guard_risk_level = str(payload.get("risk_level", "low"))
        state.input_guard_reason = payload.get("risk_reason")
        safe_query = payload.get("safe_query", state.request.query)
        if isinstance(safe_query, str) and safe_query:
            state.request.query = safe_query
        trace(
            state,
            "input_guard",
            "completed",
            "Governance input guard completed",
            decision=state.input_guard_decision,
            risk_level=state.input_guard_risk_level,
        )

    def _run_output_guard(self, state: GraphState) -> None:
        response = state.provider_response
        classification = state.classification
        assert response is not None
        assert classification is not None
        trace(state, "output_guard", "entered", "Calling governance output guard")
        citations = [
            knowledge_citation_to_governance(citation, {})
            for citation in state.retrieved_citations
        ]
        retrieved_chunks = [snippet.content for snippet in state.request.source_snippets]
        payload = self.governance.output_guard(
            request_id=state.request.request_id,
            answer=response.answer,
            cautions=response.warnings,
            citations=citations,
            risk_level=classification.risk.value,
            user_role=state.request.user_role,
            retrieved_document_ids=state.retrieved_document_ids,
            retrieved_chunks=retrieved_chunks,
            retry_count=state.regeneration_count,
            token_metrics={
                "tokens_before_optimization": state.metrics.token_count_before,
                "tokens_after_optimization": state.metrics.token_count_after,
                "tokens_saved": max(0, state.metrics.token_count_before - state.metrics.token_count_after),
                "optimization_method": "headroom"
                if state.optimized_context and state.optimized_context.headroom_used
                else "deterministic"
                if state.optimized_context
                else "none",
            },
        )
        state.output_guard_decision = str(payload.get("decision", "pass"))
        state.output_guard_failure_reasons = list(payload.get("failure_reasons", []))
        response.answer = payload.get("answer") or response.answer
        response.warnings = list(payload.get("cautions", response.warnings))
        trace(
            state,
            "output_guard",
            "completed",
            "Governance output guard completed",
            decision=state.output_guard_decision,
            failure_count=len(state.output_guard_failure_reasons),
        )

    def _emit_analytics(
        self,
        state: GraphState,
        event_type: str,
        properties: dict[str, object],
        token_metrics: dict[str, object] | None = None,
        latency_metrics: dict[str, object] | None = None,
    ) -> None:
        try:
            self.governance.analytics_capture(
                request_id=state.request.request_id,
                event_type=event_type,
                user_role=state.request.user_role,
                session_id=state.request.session_id,
                properties=properties,
                token_metrics=token_metrics,
                latency_metrics=latency_metrics,
            )
        except Exception as exc:  # noqa: BLE001
            trace(state, "analytics", "failed", "Governance analytics capture failed", error=str(exc))

    def _decide(self, state: GraphState) -> None:
        classification = state.classification
        response = state.provider_response
        assert classification is not None
        assert response is not None

        should_escalate = classification.risk.value == "high" or state.leakage_detected
        should_regenerate = False
        rationale = "Normal completion."
        final_status = "completed"

        if state.output_guard_decision == "block":
            final_status = "blocked_by_output_guard"
            rationale = "Governance output guard blocked the answer."
        elif state.output_guard_decision == "escalate":
            should_escalate = True
            final_status = "escalated"
            rationale = "Governance output guard requested escalation."
        elif state.output_guard_decision == "regenerate" and state.regeneration_count < self.settings.max_regenerations:
            should_regenerate = True
            final_status = "regenerating"
            rationale = "Governance output guard requested one controlled regeneration."
        elif state.output_guard_decision == "regenerate":
            should_escalate = True
            final_status = "escalated"
            rationale = "Governance validation still failed after the controlled regeneration."
        elif should_escalate:
            final_status = "escalated"
            rationale = "High-risk classification or leakage detection requires escalation."
        elif "empty response" in response.answer.lower():
            if state.regeneration_count < self.settings.max_regenerations:
                should_regenerate = True
                final_status = "regenerating"
                rationale = "Provider returned an empty answer."
            else:
                should_escalate = True
                final_status = "escalated"
                rationale = "Provider remained empty after the controlled regeneration."
        elif not response.source_ids and state.request.source_snippets:
            if state.regeneration_count < self.settings.max_regenerations:
                should_regenerate = True
                final_status = "regenerating"
                rationale = "Response lost source attribution."
            else:
                should_escalate = True
                final_status = "escalated"
                rationale = "Source attribution remained missing after regeneration."

        state.decision = GraphDecision(
            should_escalate=should_escalate,
            should_regenerate=should_regenerate,
            final_status=final_status,
            rationale=rationale,
        )
        trace(
            state,
            "decision",
            "completed",
            "Decision computed",
            should_escalate=should_escalate,
            should_regenerate=should_regenerate,
            rationale=rationale,
        )

    def _regenerate_once(self, state: GraphState) -> None:
        state.regeneration_count += 1
        trace(state, "regenerate", "entered", "Running single controlled regeneration")
        query = f"{state.request.query}\n\nPlease preserve citations and state uncertainty explicitly."
        state.request.query = query
        self._generate(state)
        self._run_output_guard(state)
        self._decide(state)
        if state.decision.final_status == "completed":
            state.decision.final_status = "completed_after_regeneration"
        trace(
            state,
            "regenerate",
            "completed",
            "Controlled regeneration completed",
            validation_status=state.output_guard_decision,
        )

    def _write_cache_if_allowed(self, state: GraphState) -> None:
        if state.decision.final_status not in {"completed", "completed_after_regeneration"}:
            return
        if state.output_guard_decision not in {"pass", "pass_with_warning"}:
            return
        if state.evidence_status != "sufficient" or state.leakage_detected:
            return
        response = state.provider_response
        if response is None or not state.retrieved_citations:
            return
        try:
            result = self.knowledge.cache_write(
                query=state.request.query,
                role=state.request.user_role,
                status=state.request.status_filter,
                answer=response.answer,
                citations=state.retrieved_citations,
                validation_status=state.output_guard_decision,
            )
            trace(
                state,
                "cache_write",
                "completed",
                "Validated answer stored in semantic cache",
                stored=result.get("stored", False),
            )
        except Exception as exc:  # noqa: BLE001
            trace(state, "cache_write", "failed", "Semantic cache write failed", error=str(exc))
