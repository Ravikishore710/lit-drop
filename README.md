# Scientific Multimodal Document Intelligence System

A production-grade AI system that ingests scientific and technical documents (PDFs), parses them into a canonical multimodal structured representation, indexes their textual, visual, structural, and relational features, and enables grounded question-answering with verifiable citations.

---

## 1. System Capabilities

- **Multimodal Document Parsing**: High-fidelity page rasterization (150 DPI), reading-order reconstruction, and element extraction for titles, section headings, paragraphs, tables, figures, charts, equations, and references.
- **Canonical Representation**: Stable machine-readable format independent of downstream databases (`documents/`, `pages/`, `elements/`, and `relations/` in JSONL).
- **Hybrid Retrieval**: Dense ANN vector search (Qdrant + HNSW + SQ8 quantization) and Lexical search (BM25) fused via Reciprocal Rank Fusion (RRF).
- **Relational Document Graph**: Graph modeling (Neo4j / NetworkX) tracking section hierarchies, document-to-document citations, and entity links.
- **Strict Evidence Grounding**: Strict citation verifier that rejects hallucinated citations and classifies answers as `FOUND`, `PARTIALLY_SUPPORTED`, `INFERRED`, `NOT_FOUND`, `AMBIGUOUS`, or `CONTRADICTORY`.
- **Ultra-Clean Research Studio UI**: Light-themed web interface with PDF page viewer, interactive bounding-box overlays, element inspection, and citation navigation.

---

## 2. Project Directory Layout

```
scientific-document-intelligence/
├── src/
│   ├── config/             # Pydantic Settings & environment loader
│   ├── common/             # Structured logger, SHA-256 hashing, enums, custom exceptions
│   ├── ingestion/          # PDF file validator, PyMuPDF page renderer, element extractor
│   ├── parsing/            # Canonical document models & JSONL serializer
│   ├── layout/             # Bounding box & reading order models
│   ├── text/               # Semantic hierarchical chunker (Doc -> Sec -> Para -> Chunk)
│   ├── tables/             # Table structure & cell detection
│   ├── figures/            # Figure crops & visual descriptions
│   ├── charts/             # Chart series & axis extraction
│   ├── equations/          # Equation crops & numbering
│   ├── graph/              # Neo4j and NetworkX document graph builder
│   ├── embeddings/         # EmbeddingProvider abstraction (BGE / SentenceTransformers)
│   ├── vectorstore/        # Qdrant client with HNSW and SQ8 scalar quantization
│   ├── retrieval/          # BM25, Qdrant search, and Reciprocal Rank Fusion (RRF)
│   ├── reranking/          # Cross-Encoder reranker (ms-marco-MiniLM-L-6-v2)
│   ├── routing/            # Query intent router & retrieval planner
│   ├── llm/                # Gemini 1.5 Flash adapter & Local quantized model adapter
│   ├── grounding/          # Evidence bundler, Citation verifier, and status classifier
│   ├── evaluation/         # Metrics (Recall@K, MRR, NDCG@10)
│   └── api/                # FastAPI backend & asynchronous ingestion worker
├── frontend/               # Premium Light-themed Research Studio (HTML5/CSS3/ES6)
├── configs/
│   ├── development/        # Category distribution & local settings
│   ├── benchmark/          # DocLayNet, PubTables-1M, ChartQA configs
│   └── production/         # Production deployment config
├── notebooks/              # Standalone runnable Kaggle & Google Colab notebooks
│   ├── 01_dataset_audit.ipynb
│   ├── 02_pdf_ingestion.ipynb
│   ├── 03_layout_validation.ipynb
│   ├── 04_table_validation.ipynb
│   ├── 05_chart_validation.ipynb
│   ├── 06_embedding_benchmark.ipynb
│   ├── 07_retrieval_benchmark.ipynb
│   ├── 08_llm_benchmark.ipynb
│   └── 09_end_to_end_eval.ipynb
├── scripts/
│   ├── download_arxiv.py       # arXiv metadata & PDF bulk acquisition
│   ├── download_benchmarks.py  # DocLayNet, PubTables-1M, ChartQA downloader
│   ├── validate_sample_corpus.py # Corpus validation milestone runner
│   └── generate_notebooks.py   # Notebook generator utility
├── data/
│   ├── manifests/          # datasets.yaml (licensing, provenance, checksums)
│   ├── schemas/            # canonical_document.json schema
│   ├── raw/                # Downloaded PDFs
│   ├── intermediate/       # Rendered page PNGs and element crops
│   ├── canonical/          # Canonical JSON & JSONL records
│   └── evaluation/         # Curated QA benchmarks
├── tests/
│   └── unit/               # Automated unit tests (pytest)
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
└── LICENSE
```

---

## 3. First Milestone Verification Results

The initial foundation milestone (Section 78) was completed on **20 real scientific papers** across Computer Science/AI, Physics, Mathematics, Engineering, Statistics, and Quantitative Biology:

| Metric | Result |
|---|---|
| **Papers Validated** | **20 / 20 (100% Success)** |
| **Total Pages Rendered (150 DPI)** | **434 Pages** |
| **Multimodal Elements Extracted** | **13,242 Elements** |
| **Tables Detected & Structured** | **211 Tables** |
| **Figures Detected & Cropped** | **351 Figures** |
| **Document Graph Relations** | **16,182 Edges** |
| **Validation Summary Report** | `data/canonical/validation_summary.json` |

Sample papers validated include landmark publications:
- *Attention Is All You Need* (`1706.03762`)
- *Deep Residual Learning for Image Recognition - ResNet* (`1512.03385`)
- *BERT: Pre-training of Deep Bidirectional Transformers* (`1810.04805`)
- *Adam: A Method for Stochastic Optimization* (`1412.6980`)
- *Neural Ordinary Differential Equations* (`1806.07366`)

---

## 4. Quickstart Guide

### 4.1 Local Installation (Hardware-Optimized)

The codebase runs locally with zero mandatory Docker dependencies by defaulting to embedded in-process Qdrant (`:memory:`) and in-memory NetworkX graph:

```bash
# 1. Clone or navigate to the repository
cd scientific-document-intelligence

# 2. Install dependencies
pip install -e .

# 3. Run unit tests
pytest tests/unit

# 4. Start the FastAPI backend
uvicorn src.api.main:app --reload --port 8000
```

### 4.2 Frontend Launch

Open `frontend/index.html` in any web browser, or serve it with Python:
```bash
cd frontend
python -m http.server 3000
```
Then visit `http://localhost:3000`.

### 4.3 Docker Compose Deployment

To deploy the full production stack (FastAPI + Frontend + Qdrant + Neo4j):
```bash
docker compose up -d
```

---

## 5. Teammate Handoff & Cloud Execution (Colab / Kaggle)

For GPU-heavy benchmarks and scaling to the 2,000–10,000 paper targets:
1. Open the notebooks in `notebooks/`:
   - `01_dataset_audit.ipynb`: Metadata audit & category distributions.
   - `02_pdf_ingestion.ipynb`: High-fidelity PyMuPDF rendering benchmark.
   - `03_layout_validation.ipynb`: DocLayNet layout benchmark.
   - `04_table_validation.ipynb`: PubTables-1M table extraction evaluation.
   - `05_chart_validation.ipynb`: ChartQA / ChartQAPro visual reasoning.
   - `06_embedding_benchmark.ipynb`: FP32 vs SQ8 scalar quantization tradeoff.
   - `07_retrieval_benchmark.ipynb`: Recall@K, MRR, and NDCG@10 metrics.
   - `08_llm_benchmark.ipynb`: Cloud LLM vs Quantized Local LLM comparison.
   - `09_end_to_end_eval.ipynb`: Full ablation matrix execution.
2. Direct data links and dataset cards are listed in `data/manifests/datasets.yaml`.
