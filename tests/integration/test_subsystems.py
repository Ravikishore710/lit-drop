# Integration Tests for Multimodal Subsystems

from src.charts.pipeline import ChartPipeline
from src.equations.pipeline import EquationPipeline
from src.figures.pipeline import FigurePipeline
from src.graph.builder import DocumentGraphBuilder
from src.tables.pipeline import TablePipeline, TableStructure


def test_table_pipeline_grits_and_markdown():
    table = TableStructure(
        columns=["Model", "BLEU", "FLOPs"],
        rows=[
            ["Transformer-Base", "27.3", "3.3e18"],
            ["Transformer-Big", "28.4", "2.3e19"],
        ],
    )
    md = TablePipeline.to_markdown(table)
    assert "| Model | BLEU | FLOPs |" in md
    assert "| Transformer-Big | 28.4 | 2.3e19 |" in md

    # GriTS metric test
    gold_rows = [
        ["Transformer-Base", "27.3", "3.3e18"],
        ["Transformer-Big", "28.4", "2.3e19"],
    ]
    scores = TablePipeline.compute_grits(table.rows, gold_rows)
    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0
    assert scores["f1"] == 1.0


def test_chart_pipeline_relaxed_accuracy():
    # Number within 5% tolerance
    assert ChartPipeline.compute_relaxed_accuracy("28.4", "28.0", tolerance=0.05) is True
    # Number outside 5% tolerance
    assert ChartPipeline.compute_relaxed_accuracy("35.0", "28.0", tolerance=0.05) is False
    # Text exact match
    assert ChartPipeline.compute_relaxed_accuracy("ResNet-152", "resnet-152") is True


def test_equation_pipeline():
    eq_num = EquationPipeline.extract_equation_number("Attention(Q,K,V) = softmax(QK^T / sqrt(d_k))V  (1)")
    assert eq_num == "1"

    latex = EquationPipeline.format_latex_fallback("A × B ± C")
    assert r"\times" in latex
    assert r"\pm" in latex


def test_figure_pipeline_caption_association():
    fig_bbox = (100.0, 100.0, 400.0, 300.0)
    captions = [
        {"bounding_box": (100.0, 50.0, 400.0, 70.0), "normalized_content": "Top Header"},
        {"bounding_box": (100.0, 310.0, 400.0, 330.0), "normalized_content": "Figure 1: The Transformer Architecture."},
    ]
    caption = FigurePipeline.associate_caption_heuristic(fig_bbox, captions)
    assert caption == "Figure 1: The Transformer Architecture."


def test_graph_citation_traversal():
    graph = DocumentGraphBuilder()
    graph.local_graph.add_edge("DOC_A", "ELEM_1", relation_type="HAS_ELEMENT")
    graph.local_graph.add_edge("ELEM_1", "REF_DOC_B", relation_type="CITES")

    network = graph.get_citation_network("DOC_A")
    assert "REF_DOC_B" in network["cited_targets"]
