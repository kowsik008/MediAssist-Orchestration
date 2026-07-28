from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, Query

from .config import get_settings
from .manifest import load_manifest
from .models import (
    CacheLookupRequest,
    CacheLookupResponse,
    CacheWriteRequest,
    CacheWriteResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from .store import KnowledgeStore

app = FastAPI(title="MediTrust AI Knowledge Service", version="1.0.0")


@lru_cache
def get_store() -> KnowledgeStore:
    return KnowledgeStore(get_settings())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    store = get_store()
    return HealthResponse(
        status="ok" if store.vector.chroma_available else "degraded",
        chroma_available=store.vector.chroma_available,
        knowledge_collection=settings.chroma_knowledge_collection,
        cache_collection=settings.chroma_cache_collection,
        persist_directory=str(settings.chroma_persist_directory),
        chroma_error=store.vector.chroma_error,
    )


@app.get("/sources")
def sources() -> list[dict]:
    settings = get_settings()
    documents = load_manifest(settings.source_manifest_path)
    catalog: list[dict] = []
    for document in documents:
        source_path = settings.source_manifest_path.parent.parent / document.file_path
        content = source_path.read_text(encoding="utf-8-sig") if source_path.is_file() else ""
        catalog.append({**document.model_dump(mode="json"), "content": content})
    return catalog


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    return get_store().ingest(request)


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    return get_store().retrieve(request)


@app.post("/cache/lookup", response_model=CacheLookupResponse)
def cache_lookup(request: CacheLookupRequest) -> CacheLookupResponse:
    return get_store().cache_lookup(request)


@app.post("/cache/write", response_model=CacheWriteResponse)
def cache_write(request: CacheWriteRequest) -> CacheWriteResponse:
    return get_store().cache_write(request)


@app.post("/cache/invalidate")
def cache_invalidate(document_id: str | None = Query(default=None)):
    return get_store().invalidate_cache(document_id=document_id)
