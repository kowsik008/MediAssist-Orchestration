from fastapi import APIRouter, Depends

from orchestration_service.app.config import Settings, get_settings
from orchestration_service.app.graph import OrchestrationEngine
from orchestration_service.app.langgraph_runtime import GRAPH_EDGES, GRAPH_NODES
from orchestration_service.app.models import ExampleResponse, HealthResponse, InvocationMode, InvocationRequest
from orchestration_service.app.providers import build_provider


router = APIRouter()


def get_engine(settings: Settings = Depends(get_settings)) -> OrchestrationEngine:
    return OrchestrationEngine(settings=settings, provider=build_provider(settings))


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.orchestration_env,
        provider=settings.model_provider,
        knowledge_service_base_url=settings.knowledge_service_base_url,
        governance_service_base_url=settings.governance_service_base_url,
        headroom_enabled=settings.headroom_enabled,
        headroom_available=settings.headroom_available,
        headroom_base_url=settings.headroom_base_url,
    )


@router.post("/api/v1/invoke/baseline")
def invoke_baseline(request: InvocationRequest, engine: OrchestrationEngine = Depends(get_engine)):
    return engine.run(request, InvocationMode.baseline)


@router.post("/api/v1/invoke/optimized")
def invoke_optimized(request: InvocationRequest, engine: OrchestrationEngine = Depends(get_engine)):
    return engine.run(request, InvocationMode.optimized)


@router.post("/api/v1/invoke/classify")
def classify_only(request: InvocationRequest, engine: OrchestrationEngine = Depends(get_engine)):
    response = engine.run(request, InvocationMode.baseline)
    return {
        "request_id": response.request_id,
        "classification": response.classification,
        "trace": response.trace,
    }


@router.get("/api/v1/examples", response_model=ExampleResponse)
def examples() -> ExampleResponse:
    sample_request = {
        "query": "When should healthcare workers perform hand hygiene?",
        "user_role": "nurse",
        "top_k": 5,
        "status_filter": "active",
        "source_type": "public_guideline",
    }
    sample_response = {
        "answer": "Mock response for hand hygiene guidance with knowledge-service citations.",
        "final_status": "completed",
        "warnings": [],
    }
    return ExampleResponse(requests=[sample_request], responses=[sample_response])


@router.get("/api/v1/graph")
def graph_definition():
    return {
        "nodes": GRAPH_NODES,
        "edges": GRAPH_EDGES,
    }
