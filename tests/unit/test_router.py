# Unit Tests for Query Router

from src.common.types import QueryIntent
from src.routing.classifier import QueryRouter


def test_query_routing_classification():
    router = QueryRouter()

    # Table queries
    q1 = router.classify_query("What is the accuracy of Model A in Table 2?")
    assert q1 == QueryIntent.TABLE

    # Chart queries
    q2 = router.classify_query("How does the training loss curve behave over epochs?")
    assert q2 == QueryIntent.CHART

    # Graph queries
    q3 = router.classify_query("Which papers cite the original transformer architecture?")
    assert q3 == QueryIntent.GRAPH

    # Comparison queries
    q4 = router.classify_query("Compare the performance difference between Method A and Method B")
    assert q4 == QueryIntent.COMPARISON

    # Retrieval planning
    plan_table = router.plan_retrieval(QueryIntent.TABLE)
    assert plan_table["use_tables"] is True

    plan_graph = router.plan_retrieval(QueryIntent.GRAPH)
    assert plan_graph["use_graph"] is True
