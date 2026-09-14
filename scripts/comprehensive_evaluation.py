# Comprehensive System Evaluation Harness
import json
import os
import sys
import time
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://127.0.0.1:8000"
RESULTS_FILE = Path("data/evaluation/results/live_test_suite_results.json")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)


test_results = []

def record_test(test_id, category, difficulty, query, target_doc, response_data, duration_sec, verification_notes):
    test_results.append({
        "test_id": test_id,
        "category": category,
        "difficulty": difficulty,
        "query": query,
        "target_doc": target_doc,
        "duration_sec": round(duration_sec, 2),
        "response": response_data,
        "audit": verification_notes
    })
    print(f"[{test_id}] {category} ({difficulty}) completed in {duration_sec:.2f}s")

def run_evaluation():
    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        # Test 1: Easy Factual QA
        t0 = time.time()
        q1 = "What is the dimensionality d_model of the input and output in the base Transformer architecture?"
        r1 = client.post("/api/v1/documents/1706.03762/query", json={"query": q1, "top_k": 5}).json()
        record_test("TEST_01", "Single-Doc QA", "Easy (Factual)", q1, "1706.03762", r1, time.time() - t0, "Verify d_model = 512")

        # Test 2: Medium Table & Numerical Metric QA
        t0 = time.time()
        q2 = "In Table 1 or the ImageNet classification experiments, what is the top-1 error rate of the 152-layer ResNet compared to the 34-layer plain net?"
        r2 = client.post("/api/v1/documents/1512.03385/query", json={"query": q2, "top_k": 8}).json()
        record_test("TEST_02", "Single-Doc QA", "Medium (Table/Numerical)", q2, "1512.03385", r2, time.time() - t0, "Verify ResNet-152 top-1 error vs 34-layer plain")

        # Test 3: Hard Math & Hyperparameter QA
        t0 = time.time()
        q3 = "How are the moment decay hyper-parameters beta_1 and beta_2 initialized in the Adam algorithm, and what is the default value of epsilon?"
        r3 = client.post("/api/v1/documents/1412.6980/query", json={"query": q3, "top_k": 6}).json()
        record_test("TEST_03", "Single-Doc QA", "Hard (Math/Hyperparameters)", q3, "1412.6980", r3, time.time() - t0, "Verify beta_1=0.9, beta_2=0.999, eps=1e-8")

        # Test 4: Adversarial Negative Test (Anti-Hallucination Trap)
        t0 = time.time()
        q4 = "What was the accuracy of the Transformer when evaluated on the ImageNet-1K computer vision dataset using quantum annealing?"
        r4 = client.post("/api/v1/documents/1706.03762/query", json={"query": q4, "top_k": 5}).json()
        record_test("TEST_04", "Single-Doc QA", "Adversarial (Hallucination Trap)", q4, "1706.03762", r4, time.time() - t0, "System MUST NOT hallucinate; must state no evidence or return NOT_FOUND")

        # Test 5: Tricky Multi-Condition Nuance QA
        t0 = time.time()
        q5 = "What numerical ODE solver is used by default in Neural ODEs, and how is the gradient computed without storing intermediate forward states?"
        r5 = client.post("/api/v1/documents/1806.07366/query", json={"query": q5, "top_k": 6}).json()
        record_test("TEST_05", "Single-Doc QA", "Tricky (Multi-Concept Nuance)", q5, "1806.07366", r5, time.time() - t0, "Verify dopri5/Runge-Kutta and Adjoint Sensitivity Method")

        # Test 6: Multi-Document Comparison (2 Papers)
        t0 = time.time()
        q6 = "Compare the self-attention masking mechanism in the original Transformer decoder versus BERT's bidirectional attention during pre-training."
        r6 = client.post("/api/v1/compare", json={"document_ids": ["1706.03762", "1810.04805"], "query": q6, "top_k": 8}).json()
        record_test("TEST_06", "Multi-Doc Compare", "Hard (Cross-Paper Synthesis)", q6, ["1706.03762", "1810.04805"], r6, time.time() - t0, "Verify causal mask vs bidirectional Masked LM")

        # Test 7: Tri-Paper Comparative Analysis (3 Papers)
        t0 = time.time()
        q7 = "How does the optimization strategy in Transformer (Adam with warmup) compare to the optimization used in ResNet (SGD with momentum)?"
        r7 = client.post("/api/v1/compare", json={"document_ids": ["1706.03762", "1512.03385", "1412.6980"], "query": q7, "top_k": 10}).json()
        record_test("TEST_07", "Multi-Doc Compare", "Complex (Tri-Paper Synthesis)", q7, ["1706.03762", "1512.03385", "1412.6980"], r7, time.time() - t0, "Verify Adam warmup vs SGD momentum")

        # Test 8: Hybrid Search (Conceptual Semantic)
        t0 = time.time()
        q8 = "vanishing gradient problem in very deep neural networks and residual learning"
        r8 = client.post("/api/v1/search", json={"query": q8, "top_k": 5}).json()
        record_test("TEST_08", "Hybrid Search", "Medium (Semantic Concept)", q8, "Global", {"hits_count": len(r8), "top_hit": r8[0] if r8 else None}, time.time() - t0, "Verify ResNet chunks ranked highest")

        # Test 9: Hybrid Search (Exact Mathematical Formula)
        t0 = time.time()
        q9 = "softmax((QK^T) / sqrt(d_k))"
        r9 = client.post("/api/v1/search", json={"query": q9, "top_k": 5}).json()
        record_test("TEST_09", "Hybrid Search", "Tricky (Exact Math Symbols)", q9, "Global", {"hits_count": len(r9), "top_hit": r9[0] if r9 else None}, time.time() - t0, "Verify exact equation matched in Transformer chunks")

        # Test 10: Citation Graph Subgraph Traversal
        t0 = time.time()
        r10 = client.get("/api/v1/documents/1706.03762/graph").json()
        record_test("TEST_10", "Graph Retrieval", "Medium (Structural Traversal)", "Fetch Subgraph", "1706.03762", {"nodes_count": len(r10.get("nodes", [])), "edges_count": len(r10.get("edges", []))}, time.time() - t0, "Verify node and edge counts")

        # Test 11: Visual Page Streaming & Crop Check
        t0 = time.time()
        page_res = client.get("/api/v1/documents/1706.03762/pages/1")
        record_test("TEST_11", "Visual Multimodal", "Easy (Page Streaming)", "Page 1 PNG", "1706.03762", {"status_code": page_res.status_code, "content_type": page_res.headers.get("content-type"), "bytes": len(page_res.content)}, time.time() - t0, "Verify valid 150 DPI PNG")

        # Test 12: Dual Engine Head-to-Head (Local Qwen2.5 vs Cloud Gemini)
        from src.llm.adapter import LLMOrchestrator
        orch = LLMOrchestrator()
        test_evidence = "[SRC_01] The Transformer uses scaled dot-product attention where the scaling factor is the square root of the key dimension d_k. [SRC_02] In the base model, d_model is set to 512 and number of heads h is 8."
        test_q = "Why is the dot product scaled, and what is the dimension d_model?"
        
        t0 = time.time()
        cloud_ans = orch.generate_grounded_answer(test_q, test_evidence, force_local=False)
        cloud_time = time.time() - t0
        
        t0 = time.time()
        local_ans = orch.generate_grounded_answer(test_q, test_evidence, force_local=True)
        local_time = time.time() - t0
        
        record_test("TEST_12", "Engine Parity", "Hard (Dual Engine Comparison)", test_q, "Synthetic Grounding", {
            "gemini_3_6_flash": {"answer": cloud_ans, "latency_sec": round(cloud_time, 2)},
            "qwen_2_5_0_5b_local": {"answer": local_ans, "latency_sec": round(local_time, 2)}
        }, cloud_time + local_time, "Compare citation retention and output fidelity between Cloud & Local")

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    print(f"All 12 evaluation tests completed and saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_evaluation()
