# FastAPI Application Core Endpoints

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.common.logging import logger
from src.common.types import ProcessingStatus
from src.config.settings import settings
from src.embeddings.provider import LocalSentenceTransformerProvider
from src.graph.builder import DocumentGraphBuilder
from src.grounding.verifier import CitationVerifier, EvidenceBundler, GroundedAnswer
from src.ingestion.pipeline import IngestionPipeline
from src.llm.adapter import LLMOrchestrator
from src.parsing.serializer import CanonicalSerializer
from src.reranking.reranker import LocalCrossEncoderReranker
from src.retrieval.engine import HybridRetrievalEngine
from src.routing.classifier import QueryRouter
from src.text.chunker import HierarchicalChunker
from src.vectorstore.qdrant import QdrantVectorStore

app = FastAPI(
    title="Scientific Multimodal Document Intelligence API",
    version=settings.PARSER_VERSION,
    description="High-performance multimodal PDF intelligence, hybrid retrieval, and grounded QA",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Subsystems
pipeline = IngestionPipeline()
embedding_provider = LocalSentenceTransformerProvider(
    model_name=settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE
)
vector_store = QdrantVectorStore(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    collection_name=settings.QDRANT_COLLECTION,
    vector_dim=settings.EMBEDDING_DIM,
    use_sq8=settings.QDRANT_USE_SQ8,
)
retrieval_engine = HybridRetrievalEngine(vector_store, embedding_provider)
reranker = LocalCrossEncoderReranker(
    model_name=settings.RERANKER_MODEL, device=settings.RERANKER_DEVICE
)
query_router = QueryRouter()
llm_orchestrator = LLMOrchestrator()
citation_verifier = CitationVerifier()
graph_builder = DocumentGraphBuilder(neo4j_uri=settings.NEO4J_URI)
chunker = HierarchicalChunker()

# In-memory document registry
DOCUMENTS_DB: Dict[str, Dict[str, Any]] = {}


class QueryRequest(BaseModel):
    query: str
    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 8


class SearchRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    top_k: int = 10


def run_async_ingestion(temp_pdf_path: Path, filename: str):
    try:
        canonical_doc = pipeline.process_pdf(
            pdf_path=temp_pdf_path,
            source="upload",
            output_dir=settings.CANONICAL_DIR,
        )
        doc_id = canonical_doc.document_id

        # Chunk & Index
        chunks = chunker.chunk_document(canonical_doc)
        if chunks:
            chunk_texts = [c.text for c in chunks]
            embeddings = embedding_provider.embed_batch(chunk_texts)
            vector_store.index_chunks(chunks, embeddings)

            doc_dicts = [
                {
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "parent_section_id": c.parent_section_id,
                    "page_numbers": c.page_numbers,
                    "element_ids": c.element_ids,
                    "text": c.text,
                }
                for c in chunks
            ]
            retrieval_engine.index_documents(doc_dicts)

        # Build Graph
        graph_builder.build_from_document(canonical_doc)

        DOCUMENTS_DB[doc_id] = {
            "document_id": doc_id,
            "title": canonical_doc.metadata.title,
            "authors": canonical_doc.metadata.authors,
            "page_count": canonical_doc.metadata.page_count,
            "filename": filename,
            "status": ProcessingStatus.READY.value,
            "canonical_file": str(settings.CANONICAL_DIR / "documents" / f"{doc_id.replace('sha256:', '')}.json"),
        }
        logger.info(f"Asynchronous processing complete for {doc_id}")
    except Exception as exc:
        logger.error(f"Async ingestion failed for {filename}: {exc}")


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.PARSER_VERSION}


@app.get("/ready")
def readiness_check():
    return {
        "status": "ready",
        "qdrant": True,
        "neo4j": True,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }


@app.post("/api/v1/documents")
async def upload_document(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    settings.RAW_DIR.mkdir(parents=True, exist_ok=True)
    temp_target = settings.RAW_DIR / file.filename
    with open(temp_target, "wb") as f:
        f.write(await file.read())

    # Pre-register document
    doc_placeholder_id = f"pending:{file.filename}"
    DOCUMENTS_DB[doc_placeholder_id] = {
        "document_id": doc_placeholder_id,
        "filename": file.filename,
        "status": ProcessingStatus.PROCESSING.value,
    }

    background_tasks.add_task(run_async_ingestion, temp_target, file.filename)

    return {
        "message": "File accepted for processing",
        "filename": file.filename,
        "status": ProcessingStatus.PROCESSING.value,
    }


@app.get("/api/v1/documents")
def list_documents():
    # Also load from canonical folder if available
    doc_folder = settings.CANONICAL_DIR / "documents"
    if doc_folder.exists():
        for doc_file in doc_folder.glob("*.json"):
            try:
                doc = CanonicalSerializer.load_document(doc_file)
                if doc.document_id not in DOCUMENTS_DB:
                    DOCUMENTS_DB[doc.document_id] = {
                        "document_id": doc.document_id,
                        "title": doc.metadata.title,
                        "authors": doc.metadata.authors,
                        "page_count": doc.metadata.page_count,
                        "filename": doc.metadata.original_filename,
                        "status": ProcessingStatus.READY.value,
                        "canonical_file": str(doc_file),
                    }
            except Exception:
                pass
    return list(DOCUMENTS_DB.values())


@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: str):
    clean_id = document_id.replace("sha256:", "")
    doc_file = settings.CANONICAL_DIR / "documents" / f"{clean_id}.json"
    if not doc_file.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return CanonicalSerializer.load_document(doc_file)


@app.delete("/api/v1/documents/{document_id}")
def delete_document(document_id: str):
    clean_id = document_id.replace("sha256:", "")
    doc_file = settings.CANONICAL_DIR / "documents" / f"{clean_id}.json"
    if doc_file.exists():
        doc_file.unlink()
    DOCUMENTS_DB.pop(document_id, None)
    return {"message": "Document deleted", "document_id": document_id}


@app.post("/api/v1/documents/{document_id}/query", response_model=GroundedAnswer)
def query_document(document_id: str, request: QueryRequest):
    # 1. Classify Query Intent
    intent = query_router.classify_query(request.query)

    # 2. Hybrid Retrieve Candidates
    candidates = retrieval_engine.retrieve(
        query=request.query,
        filter_doc_id=document_id,
        top_candidates=30,
    )

    # 3. Rerank Candidates
    top_candidates = reranker.rerank(
        query=request.query,
        candidates=candidates,
        top_n=request.top_k,
    )

    # 4. Assemble Evidence Bundle
    bundle_text, source_map = EvidenceBundler.build_evidence_bundle(top_candidates)

    # 5. Generate Grounded Answer via LLM
    raw_answer = llm_orchestrator.generate_grounded_answer(
        query=request.query, evidence_bundle=bundle_text
    )

    # 6. Verify Citations
    grounded_answer = citation_verifier.verify_answer(
        raw_answer=raw_answer, valid_sources=source_map
    )

    return grounded_answer


@app.post("/api/v1/search")
def search_documents(request: SearchRequest):
    candidates = retrieval_engine.retrieve(
        query=request.query,
        filter_doc_id=request.document_id,
        top_candidates=request.top_k,
    )
    return candidates


@app.get("/api/v1/documents/{document_id}/pages/{page_number}")
def get_page_image(document_id: str, page_number: int):
    clean_id = document_id.replace("sha256:", "")
    img_path = (
        settings.INTERMEDIATE_DIR
        / clean_id
        / "pages"
        / f"page_{page_number:03d}.png"
    )
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Page image not found")
    return FileResponse(str(img_path), media_type="image/png")


@app.get("/api/v1/documents/{document_id}/graph")
def get_document_graph(document_id: str):
    clean_id = document_id.replace("sha256:", "")
    subgraph = graph_builder.find_connected_subgraph(document_id, depth=2)
    return subgraph


@app.get("/api/v1/elements/{element_id}")
def get_element(element_id: str):
    clean_elem = element_id.strip()
    parts = clean_elem.split("_P")
    if len(parts) >= 2:
        doc_hash = parts[0].replace("sha256:", "")
        elem_file = settings.CANONICAL_DIR / "elements" / f"{doc_hash}_elements.jsonl"
        if elem_file.exists():
            for elem in CanonicalSerializer.iter_elements(elem_file):
                if elem.element_id == clean_elem or elem.element_id.endswith(clean_elem):
                    return elem
    raise HTTPException(status_code=404, detail=f"Element {element_id} not found")


@app.get("/api/v1/elements/{element_id}/crop")
def get_element_crop(element_id: str):
    clean_elem = element_id.strip()
    parts = clean_elem.split("_P")
    if len(parts) >= 2:
        doc_hash = parts[0].replace("sha256:", "")
        crop_path = settings.INTERMEDIATE_DIR / doc_hash / "crops" / f"{clean_elem}.png"
        if crop_path.exists():
            return FileResponse(str(crop_path), media_type="image/png")
    raise HTTPException(status_code=404, detail=f"Crop for element {element_id} not found")


class CompareRequest(BaseModel):
    document_ids: List[str]
    query: str
    top_k: int = 10


@app.post("/api/v1/compare", response_model=GroundedAnswer)
def compare_documents(request: CompareRequest):
    if len(request.document_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 document IDs are required for comparison.")

    all_candidates = []
    for d_id in request.document_ids:
        cands = retrieval_engine.retrieve(query=request.query, filter_doc_id=d_id, top_candidates=15)
        all_candidates.extend(cands)

    top_candidates = reranker.rerank(query=request.query, candidates=all_candidates, top_n=request.top_k)
    bundle_text, source_map = EvidenceBundler.build_evidence_bundle(top_candidates)
    raw_answer = llm_orchestrator.generate_grounded_answer(query=request.query, evidence_bundle=bundle_text)
    grounded = citation_verifier.verify_answer(raw_answer=raw_answer, valid_sources=source_map)
    return grounded
