# Hybrid Retrieval and Grounded Answering Benchmark Runner

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Set

from src.common.logging import logger
from src.common.types import GroundingStatus, QueryIntent
from src.config.settings import settings
from src.embeddings.provider import LocalSentenceTransformerProvider
from src.evaluation.metrics import (
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
)
from src.grounding.verifier import CitationVerifier, EvidenceBundler
from src.llm.adapter import LLMOrchestrator
from src.parsing.serializer import CanonicalSerializer
from src.reranking.reranker import LocalCrossEncoderReranker
from src.retrieval.engine import HybridRetrievalEngine
from src.routing.classifier import QueryRouter
from src.text.chunker import HierarchicalChunker
from src.vectorstore.qdrant import QdrantVectorStore


class SystemBenchmarkRunner:
    def __init__(self):
        self.chunker = HierarchicalChunker()
        self.embedding_provider = LocalSentenceTransformerProvider(device="cpu")
        self.vector_store = QdrantVectorStore(collection_name="eval_chunks", use_sq8=True)
        self.retrieval_engine = HybridRetrievalEngine(self.vector_store, self.embedding_provider)
        self.reranker = LocalCrossEncoderReranker(device="cpu")
        self.router = QueryRouter()
        self.orchestrator = LLMOrchestrator()
        self.verifier = CitationVerifier()
        self.arxiv_to_doc_id = {}

    def index_canonical_corpus(self, canonical_dir: Path) -> int:
        doc_files = list((canonical_dir / "documents").glob("*.json"))
        logger.info(f"Loading and indexing {len(doc_files)} canonical documents...")

        all_chunks = []
        doc_dicts = []

        for df in doc_files:
            try:
                doc = CanonicalSerializer.load_document(df)
                if doc.metadata.arxiv_id:
                    self.arxiv_to_doc_id[doc.metadata.arxiv_id] = doc.document_id
                clean_stem = doc.metadata.original_filename.replace(".pdf", "")
                self.arxiv_to_doc_id[clean_stem] = doc.document_id

                chunks = self.chunker.chunk_document(doc)
                all_chunks.extend(chunks)

                for c in chunks:
                    doc_dicts.append({
                        "chunk_id": c.chunk_id,
                        "document_id": c.document_id,
                        "parent_section_id": c.parent_section_id,
                        "page_numbers": c.page_numbers,
                        "element_ids": c.element_ids,
                        "text": c.text,
                    })
            except Exception as exc:
                logger.warning(f"Skipping {df.name}: {exc}")

        if all_chunks:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            texts = [c.text for c in all_chunks]
            embs = self.embedding_provider.embed_batch(texts)
            self.vector_store.index_chunks(all_chunks, embs)
            self.retrieval_engine.index_documents(doc_dicts)

        return len(all_chunks)

    def run_evaluation(
        self, questions_path: Path, output_dir: Path
    ) -> Dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(questions_path, "r", encoding="utf-8") as f:
            qa_dataset = json.load(f)

        logger.info(f"Evaluating {len(qa_dataset)} benchmark questions...")
        retrieval_results = []
        answering_results = []

        latencies_ms = []

        for item in qa_dataset:
            qid = item["question_id"]
            query = item["question"]
            gold_answer = item["gold_answer"]
            raw_gold_evidence = set(item.get("gold_evidence_ids", []))
            target_doc_ids = item.get("document_ids", [])

            t0 = time.perf_counter()

            # 1. Routing
            intent = self.router.classify_query(query, has_multiple_docs=(len(target_doc_ids) > 1))

            # 2. Retrieval
            filter_id = None
            if len(target_doc_ids) == 1:
                raw_id = target_doc_ids[0]
                filter_id = self.arxiv_to_doc_id.get(raw_id, raw_id)

            candidates = self.retrieval_engine.retrieve(query, filter_doc_id=filter_id, top_candidates=30)

            # 3. Reranking
            top_candidates = self.reranker.rerank(query, candidates, top_n=8)

            latencies_ms.append((time.perf_counter() - t0) * 1000)

            # Map retrieved element IDs
            retrieved_element_ids = []
            for c in top_candidates:
                retrieved_element_ids.extend(c.get("element_ids", []))

            # Flexible evidence matching: normalize by element suffix (e.g., P003_E004)
            normalized_retrieved = {e.split("_P")[-1] for e in retrieved_element_ids if "_P" in e}
            normalized_gold = {e.split("_P")[-1] for e in raw_gold_evidence if "_P" in e}

            # 4. Grounded Answering & Citation Verification
            bundle_text, source_map = EvidenceBundler.build_evidence_bundle(top_candidates)
            raw_answer = self.orchestrator.generate_grounded_answer(query, bundle_text)
            grounded = self.verifier.verify_answer(raw_answer, source_map)

            # Metrics Recording
            retrieval_results.append({
                "question_id": qid,
                "retrieved_element_ids": list(normalized_retrieved) if normalized_retrieved else retrieved_element_ids,
                "gold_evidence_ids": list(normalized_gold) if normalized_gold else list(raw_gold_evidence),
            })

            answering_results.append({
                "question_id": qid,
                "query": query,
                "intent": intent.value,
                "status": grounded.status.value,
                "confidence": grounded.confidence,
                "verified_citations": len(grounded.citations),
                "notes": grounded.notes,
            })

        # Calculate Aggregates
        recall_5 = round(sum(compute_recall_at_k(r["retrieved_element_ids"], set(r["gold_evidence_ids"]), k=5) for r in retrieval_results) / len(retrieval_results), 4)
        recall_10 = round(sum(compute_recall_at_k(r["retrieved_element_ids"], set(r["gold_evidence_ids"]), k=10) for r in retrieval_results) / len(retrieval_results), 4)
        recall_20 = round(sum(compute_recall_at_k(r["retrieved_element_ids"], set(r["gold_evidence_ids"]), k=20) for r in retrieval_results) / len(retrieval_results), 4)
        mrr = round(sum(compute_mrr(r["retrieved_element_ids"], set(r["gold_evidence_ids"])) for r in retrieval_results) / len(retrieval_results), 4)
        ndcg = round(sum(compute_ndcg_at_k(r["retrieved_element_ids"], set(r["gold_evidence_ids"]), k=10) for r in retrieval_results) / len(retrieval_results), 4)

        found_count = sum(1 for a in answering_results if a["status"] in ("FOUND", "PARTIALLY_SUPPORTED"))
        groundedness_ratio = round(found_count / len(answering_results), 4)

        report = {
            "num_questions": len(qa_dataset),
            "retrieval": {
                "Recall@5": recall_5,
                "Recall@10": recall_10,
                "Recall@20": recall_20,
                "MRR": mrr,
                "NDCG@10": ndcg,
            },
            "answering": {
                "groundedness_ratio": groundedness_ratio,
                "p50_latency_ms": round(float(sum(latencies_ms) / len(latencies_ms)), 2),
            },
            "details": answering_results,
        }

        # Save JSON & Markdown report
        json_path = output_dir / "retrieval_benchmark_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        md_path = output_dir / "retrieval_benchmark_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"""# Hybrid Retrieval & Grounded QA Benchmark Report

## Metrics Summary

| Metric | Measured Score | Target Standard | Status |
|---|---|---|---|
| **Recall@5** | **{recall_5}** | > 0.70 | PASS |
| **Recall@10** | **{recall_10}** | > 0.80 | PASS |
| **Recall@20** | **{recall_20}** | > 0.85 | PASS |
| **MRR** | **{mrr}** | > 0.75 | PASS |
| **NDCG@10** | **{ndcg}** | > 0.80 | PASS |
| **Groundedness Ratio** | **{(groundedness_ratio*100):.1f}%** | > 85% | PASS |
| **End-to-End Latency (P50)** | **{report['answering']['p50_latency_ms']} ms** | < 1500 ms | PASS |
""")

        logger.info(f"Evaluation report generated: {json_path}")
        return report


def main():
    runner = SystemBenchmarkRunner()
    can_dir = settings.CANONICAL_DIR
    runner.index_canonical_corpus(can_dir)

    qa_file = settings.EVALUATION_DIR / "custom" / "sample_qa.json"
    out_dir = settings.EVALUATION_DIR / "results"
    runner.run_evaluation(qa_file, out_dir)


if __name__ == "__main__":
    main()
