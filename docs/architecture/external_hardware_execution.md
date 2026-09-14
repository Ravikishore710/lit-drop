# External Tools, Hardware Execution, and Remote Offloading Guide

This guide details how the system is engineered to operate efficiently under local hardware constraints, which operations can be offloaded to remote/cloud environments, and the exact steps for configuring external APIs and MCP servers.

---

## 1. Local Execution Architecture (Lightweight / Low RAM)

The backend has been explicitly engineered with in-memory and embedded fallback modes so that developers without high-end GPUs or large RAM capacities can run the full pipeline locally:

| Component | Local Hardware-Optimized Engine | RAM Consumption | CPU/GPU Requirement |
|---|---|---|---|
| **PDF Ingestion & Rendering** | PyMuPDF (C-backed rasterizer at 150 DPI) | ~80 MB per document | CPU only |
| **Multimodal Element Extraction** | PyMuPDF dict extraction & table detection | ~60 MB | CPU only |
| **Vector Store** | In-process Qdrant (`:memory:`) with SQ8 Scalar Quantization | ~225 KB per 600 vectors | CPU only |
| **Lexical Search** | Pure Python BM25 inverted index | ~15 MB | CPU only |
| **Document Graph** | In-memory NetworkX directed graph | ~25 MB per 20 documents | CPU only |
| **Reranking** | Compact Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) | ~120 MB | CPU only |
| **Evidence Grounding** | Rule-based regex & CitationVerifier | < 5 MB | CPU only |

**Total Local Overhead**: Under **1.2 GB RAM**, zero GPU required.

---

## 2. When to Use External Tools or Cloud Hardware

Certain operations from the master blueprint are computationally intensive and should **not** be run on a constrained local machine. These should be offloaded to cloud environments (Google Colab, Kaggle, or Remote Cloud VMs):

### 2.1 Scaling Production Corpus (2,000 to 10,000 arXiv Papers)
- **Why**: Downloading and rendering 2,000 to 10,000 PDFs requires 15–50 GB disk space and several hours of network I/O.
- **Where to Run**: Google Colab or a dedicated Linux VPS.
- **Command**:
  ```bash
  python scripts/download_arxiv.py --count 2000 --raw-dir /mnt/storage/raw
  ```

### 2.2 Benchmarking DocLayNet (20,000+ Layout Pages)
- **Why**: Training or evaluating vision object-detection models (LayoutLMv3 / YOLO-Doc) across 20,000 pages requires 16+ GB VRAM.
- **Where to Run**: Kaggle Notebook (Free dual T4 GPUs) or Google Colab (A100 / V100).
- **Notebook**: [`notebooks/03_layout_validation.ipynb`](../../notebooks/03_layout_validation.ipynb)
- **Direct Source**: [https://huggingface.co/datasets/ds4sd/DocLayNet](https://huggingface.co/datasets/ds4sd/DocLayNet)

### 2.3 Benchmarking PubTables-1M (50,000 Tables)
- **Why**: Running Microsoft Table-Transformer on 50,000 high-resolution table crops.
- **Where to Run**: Kaggle / Colab GPU runtime.
- **Notebook**: [`notebooks/04_table_validation.ipynb`](../../notebooks/04_table_validation.ipynb)
- **Direct Source**: [https://huggingface.co/datasets/bsmock/pubtables-1m](https://huggingface.co/datasets/bsmock/pubtables-1m)

### 2.4 Chart Visual Reasoning (ChartQA & ChartQAPro)
- **Why**: Multi-image vision-language models (e.g., Qwen2-VL, Idefics2, or Gemini Vision) require GPU acceleration.
- **Notebook**: [`notebooks/05_chart_validation.ipynb`](../../notebooks/05_chart_validation.ipynb)

---

## 3. External API Keys Configuration

To activate live frontier multimodal generation without using local computation:

### 3.1 Google Gemini API Key
The system uses Gemini 1.5 Flash as the primary cloud reasoning model.
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Add it to `.env`:
   ```bash
   GEMINI_API_KEY=AIzaSy...
   LLM_PROVIDER=gemini
   LLM_MODEL=gemini-1.5-flash
   ```
3. When configured, all reasoning and synthesis are executed on Google's cloud infrastructure with **zero local compute or RAM overhead**.

### 3.2 Optional Local LLM via Ollama / llama.cpp
If you prefer running a small local model (e.g., DeepSeek-R1-Distill-Qwen-1.5B quantized):
```bash
# 1. Install and run Ollama
ollama run deepseek-r1:1.5b

# 2. In .env:
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=deepseek-r1:1.5b
```

---

## 4. MCP Servers Integration (Remote Bash & Tools)

The system includes configuration for Composio and MCP tool integration:
- **Remote Bash Workbench**: Heavy batch downloads or headless evaluations can be triggered on remote containers using Composio's `COMPOSIO_REMOTE_BASH_TOOL` without using local bandwidth or disk.
- **Documentation Lookup**: The `gemini-api-docs` MCP server provides up-to-date SDK signatures and API reference guides directly in the development workflow.
