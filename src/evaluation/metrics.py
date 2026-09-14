# Retrieval and Groundedness Evaluation Metrics

import math
from typing import Dict, List, Set


def compute_recall_at_k(retrieved_ids: List[str], gold_ids: Set[str], k: int = 5) -> float:
    if not gold_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    hits = top_k.intersection(gold_ids)
    return len(hits) / len(gold_ids)


def compute_mrr(retrieved_ids: List[str], gold_ids: Set[str]) -> float:
    if not gold_ids:
        return 1.0
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in gold_ids:
            return 1.0 / rank
    return 0.0


def compute_ndcg_at_k(retrieved_ids: List[str], gold_ids: Set[str], k: int = 10) -> float:
    if not gold_ids:
        return 1.0

    dcg = 0.0
    for idx, rid in enumerate(retrieved_ids[:k]):
        if rid in gold_ids:
            dcg += 1.0 / math.log2(idx + 2)

    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(gold_ids), k)))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval_batch(
    query_results: List[Dict[str, any]], k_values: List[int] = [5, 10, 20]
) -> Dict[str, float]:
    metrics: Dict[str, float] = {f"Recall@{k}": 0.0 for k in k_values}
    metrics["MRR"] = 0.0
    metrics["NDCG@10"] = 0.0

    n = len(query_results)
    if n == 0:
        return metrics

    for item in query_results:
        retrieved = item.get("retrieved_ids", [])
        gold = set(item.get("gold_ids", []))

        for k in k_values:
            metrics[f"Recall@{k}"] += compute_recall_at_k(retrieved, gold, k=k)
        metrics["MRR"] += compute_mrr(retrieved, gold)
        metrics["NDCG@10"] += compute_ndcg_at_k(retrieved, gold, k=10)

    for key in metrics:
        metrics[key] = round(metrics[key] / n, 4)

    return metrics
