# Validation Script for Sample Corpus (20 PDFs Milestone)

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import List
import pandas as pd

from src.common.logging import logger
from src.ingestion.pipeline import IngestionPipeline
from src.parsing.serializer import CanonicalSerializer
from scripts.download_arxiv import run_acquisition


def validate_corpus(raw_dir: Path, canonical_dir: Path, intermediate_dir: Path, target_count: int = 20):
    raw_dir.mkdir(parents=True, exist_ok=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(raw_dir.glob("*.pdf"))
    if len(pdf_files) < target_count:
        logger.info(f"Only {len(pdf_files)} PDFs in {raw_dir}. Fetching up to {target_count} from arXiv...")
        config_path = Path("configs/development/arxiv_distribution.yaml")
        run_acquisition(config_path, raw_dir, target_sample_count=target_count)
        pdf_files = list(raw_dir.glob("*.pdf"))

    target_pdfs = pdf_files[:target_count]
    logger.info(f"Initiating validation pipeline on {len(target_pdfs)} sample PDFs...")

    pipeline = IngestionPipeline()
    success_count = 0
    total_pages = 0
    total_elements = 0
    total_tables = 0
    total_figures = 0
    total_relations = 0

    results_summary = []

    for idx, pdf in enumerate(target_pdfs, 1):
        try:
            logger.info(f"[{idx}/{len(target_pdfs)}] Ingesting {pdf.name}...")
            canonical_doc = pipeline.process_pdf(
                pdf_path=pdf,
                source="arxiv",
                arxiv_id=pdf.stem,
                output_dir=canonical_dir,
            )

            p_count = len(canonical_doc.pages)
            e_count = len(canonical_doc.elements)
            r_count = len(canonical_doc.relations)
            tab_count = sum(1 for e in canonical_doc.elements if e.element_type == "table")
            fig_count = sum(1 for e in canonical_doc.elements if e.element_type == "figure")

            total_pages += p_count
            total_elements += e_count
            total_tables += tab_count
            total_figures += fig_count
            total_relations += r_count
            success_count += 1

            results_summary.append({
                "document_id": canonical_doc.document_id,
                "filename": pdf.name,
                "title": canonical_doc.metadata.title,
                "pages": p_count,
                "elements": e_count,
                "tables": tab_count,
                "figures": fig_count,
                "relations": r_count,
                "status": "VALIDATED"
            })
        except Exception as exc:
            logger.error(f"Failed processing {pdf.name}: {exc}")
            results_summary.append({
                "filename": pdf.name,
                "error": str(exc),
                "status": "FAILED"
            })

    # Output Summary Table
    df_summary = pd.DataFrame(results_summary)
    summary_path = canonical_dir / "validation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print("\n" + "=" * 80)
    print(f"SAMPLE CORPUS VALIDATION REPORT (Target: {target_count})")
    print("=" * 80)
    print(f"Successfully processed: {success_count}/{len(target_pdfs)} documents")
    print(f"Total Pages Rendered:   {total_pages}")
    print(f"Total Elements Extracted:{total_elements}")
    print(f"Total Tables Detected:  {total_tables}")
    print(f"Total Figures Detected: {total_figures}")
    print(f"Total Graph Relations:  {total_relations}")
    print(f"Summary JSON saved to:  {summary_path}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Corpus Validation Runner")
    parser.add_argument("--raw-dir", type=str, default="data/raw")
    parser.add_argument("--canonical-dir", type=str, default="data/canonical")
    parser.add_argument("--intermediate-dir", type=str, default="data/intermediate")
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    validate_corpus(
        raw_dir=Path(args.raw_dir),
        canonical_dir=Path(args.canonical_dir),
        intermediate_dir=Path(args.intermediate_dir),
        target_count=args.count,
    )


if __name__ == "__main__":
    main()
