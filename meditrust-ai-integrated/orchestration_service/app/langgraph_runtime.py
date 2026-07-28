from orchestration_service.app.models import GraphEdgeDefinition, GraphNodeDefinition


GRAPH_NODES = [
    GraphNodeDefinition(name="start", description="Initialize request state and tracing."),
    GraphNodeDefinition(name="classify", description="Run deterministic classification and ambiguous fallback."),
    GraphNodeDefinition(name="optimize_context", description="Optimize context with Headroom or deterministic fallback."),
    GraphNodeDefinition(name="generate", description="Invoke the selected model provider."),
    GraphNodeDefinition(name="decision", description="Evaluate escalation and regeneration rules."),
    GraphNodeDefinition(name="regenerate", description="Run one controlled regeneration when needed."),
    GraphNodeDefinition(name="finish", description="Return final response and metrics."),
]


GRAPH_EDGES = [
    GraphEdgeDefinition(source="start", target="classify"),
    GraphEdgeDefinition(source="classify", target="optimize_context", condition="mode == optimized"),
    GraphEdgeDefinition(source="classify", target="generate", condition="mode == baseline"),
    GraphEdgeDefinition(source="optimize_context", target="generate"),
    GraphEdgeDefinition(source="generate", target="decision"),
    GraphEdgeDefinition(source="decision", target="regenerate", condition="should_regenerate and regeneration_count < max_regenerations"),
    GraphEdgeDefinition(source="decision", target="finish", condition="not should_regenerate"),
    GraphEdgeDefinition(source="regenerate", target="finish"),
]
