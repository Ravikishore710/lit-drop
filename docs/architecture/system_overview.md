# Scientific Multimodal Document Intelligence System — Architecture & Engineering Overview

## 1. Executive Summary
This system provides an end-to-end multimodal document intelligence pipeline designed specifically for scientific and technical literature (PDFs). It converts complex, multi-column scientific publications into a canonical, machine-readable structured representation, indexes their textual, visual, structural, and relational features, and enables evidence-grounded reasoning through hybrid retrieval and LLM orchestration.

## 2. Pipeline Flow
```
PDF Input
  │
  ▼
[File Validation & SHA-256 Hashing] ──► Deduplication & Provenance
  │
  ▼
[High-Fidelity Page Rendering] ───────► Page PNGs (150 DPI) + Coordinate Scaler
  │
  ▼
[Layout Analysis & Extraction] ───────► Text Blocks, Headings, Tables, Figures, Equations
  │
  ▼
[Canonical Document Builder] ─────────► documents/, pages/, elements/, relations/ (.jsonl)
  │
  ├───────────────────────────────┬───────────────────────────────┐
  ▼                               ▼                               ▼
[Hierarchical Semantic Chunker] [Document Graph Builder]     [Multimodal Asset Crops]
  │                               │                               │
  ▼                               ▼                               ▼
[Vector Store: Qdrant HNSW+SQ8]  [Graph Store: Neo4j / NetworkX] [File/Object Storage]
  │                               │
  └───────────────┬───────────────┘
                  │
                  ▼
         [Query Classification] (QueryRouter: Table, Chart, Equation, Graph, Factual)
                  │
                  ▼
         [Hybrid Retrieval Engine]
                  ├── Dense Semantic Search (Cosine ANN via Qdrant)
                  ├── Lexical BM25 Search
                  └── Reciprocal Rank Fusion (RRF, k=60)
                  │
                  ▼
         [Cross-Encoder Reranker] (ms-marco-MiniLM-L-6-v2)
                  │
                  ▼
         [Evidence Bundler & LLM Orchestrator] (Gemini 1.5 Flash / Local Quantized)
                  │
                  ▼
         [Strict Citation Verification & Grounding Classifier]
         (FOUND, PARTIALLY_SUPPORTED, INFERRED, NOT_FOUND, AMBIGUOUS, CONTRADICTORY)
```

## 3. Data Contracts
- **Canonical Schema**: Defined in `data/schemas/canonical_document.json`.
- **Primary Document Key**: `sha256:<digest>`.
- **Element Object**: Bounding box `[x0, y0, x1, y1]`, reading order index, element type enum, parent section reference, and structured table data.
- **Provenance System**: All external datasets tracked in `data/manifests/datasets.yaml` with licensing terms and checksums.

## 4. Hardware Optimization & Deployment
- Designed for local execution with hardware constraints (lightweight in-memory embedded Qdrant and NetworkX fallback) while fully compatible with Dockerized Qdrant and Neo4j for scale.
- GPU-heavy benchmarking and fine-tuning supported via runnable Google Colab and Kaggle notebooks in `notebooks/`.
