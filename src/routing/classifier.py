# Query Intent Classification and Retrieval Planner

import re
from typing import Dict, List
from src.common.types import QueryIntent


class QueryRouter:
    TABLE_PATTERN = re.compile(r"\b(table|row|column|f1|accuracy|dataset|benchmark|metric|score)\b", re.IGNORECASE)
    CHART_PATTERN = re.compile(r"\b(chart|plot|curve|axis|trend|increase|decrease|percentage|bar chart)\b", re.IGNORECASE)
    FIGURE_PATTERN = re.compile(r"\b(figure|diagram|architecture|flowchart|image|pipeline|schematic)\b", re.IGNORECASE)
    EQUATION_PATTERN = re.compile(r"\b(equation|formula|loss function|derive|mathematical|theorem|proof)\b", re.IGNORECASE)
    COMPARISON_PATTERN = re.compile(r"\b(compare|versus|vs|difference between|outperform|better than)\b", re.IGNORECASE)
    GRAPH_PATTERN = re.compile(r"\b(cite|cited by|reference|who wrote|author|paper network|connected)\b", re.IGNORECASE)

    def classify_query(self, query: str, has_multiple_docs: bool = False) -> QueryIntent:
        text = query.strip()
        if not text:
            return QueryIntent.NOT_FOUND

        if self.GRAPH_PATTERN.search(text):
            return QueryIntent.GRAPH
        if has_multiple_docs or self.COMPARISON_PATTERN.search(text):
            return QueryIntent.COMPARISON
        if self.TABLE_PATTERN.search(text):
            return QueryIntent.TABLE
        if self.CHART_PATTERN.search(text):
            return QueryIntent.CHART
        if self.FIGURE_PATTERN.search(text):
            return QueryIntent.FIGURE
        if self.EQUATION_PATTERN.search(text):
            return QueryIntent.EQUATION

        words = text.split()
        if len(words) > 12 or any(w.lower() in ("why", "explain", "how", "describe") for w in words[:2]):
            return QueryIntent.EXPLANATION

        return QueryIntent.FACTUAL

    def plan_retrieval(self, intent: QueryIntent) -> Dict[str, bool]:
        plan = {
            "use_dense": True,
            "use_lexical": True,
            "use_graph": False,
            "use_tables": False,
            "use_figures": False,
        }

        if intent == QueryIntent.GRAPH:
            plan["use_graph"] = True
        elif intent == QueryIntent.TABLE:
            plan["use_tables"] = True
        elif intent in (QueryIntent.CHART, QueryIntent.FIGURE):
            plan["use_figures"] = True
        elif intent == QueryIntent.COMPARISON:
            plan["use_graph"] = True
            plan["use_tables"] = True

        return plan
