# Document Graph Builder and Neo4j Connector

from typing import Any, Dict, List, Optional
import networkx as nx

from src.common.logging import logger
from src.config.settings import settings
from src.parsing.models import CanonicalDocument, RelationObject


class DocumentGraphBuilder:
    def __init__(self, neo4j_uri: Optional[str] = None):
        self.neo4j_uri = neo4j_uri or settings.NEO4J_URI
        self.local_graph = nx.DiGraph()
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                )
                self._driver.verify_connectivity()
            except Exception:
                self._driver = False
        return self._driver

    def build_from_document(self, doc: CanonicalDocument) -> nx.DiGraph:
        # Document Node
        self.local_graph.add_node(
            doc.document_id,
            type="Document",
            title=doc.metadata.title,
            arxiv_id=doc.metadata.arxiv_id,
            pages=doc.metadata.page_count,
        )

        # Page Nodes
        for page in doc.pages:
            self.local_graph.add_node(
                page.page_id,
                type="Page",
                page_number=page.page_number,
                width=page.width,
                height=page.height,
            )

        # Element Nodes
        for elem in doc.elements:
            self.local_graph.add_node(
                elem.element_id,
                type="Element",
                element_type=elem.element_type.value,
                page_number=elem.page_number,
                reading_order=elem.reading_order,
                content_preview=elem.normalized_content[:120],
            )

        # Relations
        for rel in doc.relations:
            self.local_graph.add_edge(
                rel.source_id,
                rel.target_id,
                relation_type=rel.relation_type.value,
                **rel.metadata,
            )

        logger.info(
            f"Graph updated for {doc.document_id}: "
            f"{self.local_graph.number_of_nodes()} nodes, {self.local_graph.number_of_edges()} edges"
        )
        return self.local_graph

    def sync_to_neo4j(self, doc: CanonicalDocument) -> bool:
        driver = self._get_driver()
        if not driver:
            logger.info("Neo4j driver not connected. Graph remains in-memory.")
            return False

        with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Create Document Node
            session.run(
                """
                MERGE (d:Document {id: $doc_id})
                SET d.title = $title, d.arxiv_id = $arxiv_id, d.pages = $pages
                """,
                doc_id=doc.document_id,
                title=doc.metadata.title,
                arxiv_id=doc.metadata.arxiv_id,
                pages=doc.metadata.page_count,
            )

            # Create Elements and Edges
            for rel in doc.relations:
                session.run(
                    f"""
                    MERGE (a:Node {{id: $source_id}})
                    MERGE (b:Node {{id: $target_id}})
                    MERGE (a)-[r:{rel.relation_type.value}]->(b)
                    """,
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                )
        logger.info(f"Successfully synchronized {doc.document_id} graph into Neo4j.")
        return True

    def find_connected_subgraph(self, element_id: str, depth: int = 2) -> Dict[str, Any]:
        if element_id not in self.local_graph:
            return {"nodes": [], "edges": []}

        subgraph_nodes = set([element_id])
        frontier = {element_id}
        for _ in range(depth):
            next_frontier = set()
            for node in frontier:
                next_frontier.update(self.local_graph.predecessors(node))
                next_frontier.update(self.local_graph.successors(node))
            subgraph_nodes.update(next_frontier)
            frontier = next_frontier

        subgraph = self.local_graph.subgraph(subgraph_nodes)
        nodes = [{"id": n, **subgraph.nodes[n]} for n in subgraph.nodes]
        edges = [
            {"source": u, "target": v, **subgraph.edges[u, v]}
            for u, v in subgraph.edges
        ]
        return {"nodes": nodes, "edges": edges}

    def find_citation_path(self, source_id: str, target_id: str) -> List[str]:
        if source_id in self.local_graph and target_id in self.local_graph:
            try:
                return nx.shortest_path(self.local_graph, source=source_id, target=target_id)
            except nx.NetworkXNoPath:
                return []
        return []

    def get_citation_network(self, doc_id: str) -> Dict[str, List[str]]:
        citing_elements = []
        cited_targets = []
        if doc_id in self.local_graph:
            for succ in self.local_graph.successors(doc_id):
                for edge_target in self.local_graph.successors(succ):
                    edge_data = self.local_graph.get_edge_data(succ, edge_target)
                    if edge_data and edge_data.get("relation_type") == "CITES":
                        cited_targets.append(edge_target)
        return {
            "document_id": doc_id,
            "cited_targets": list(set(cited_targets)),
        }

