# Benchmark Datasets Acquisition Script

import argparse
from pathlib import Path
from typing import Optional
from src.common.logging import logger

BENCHMARK_RESOURCES = {
    "doclaynet": {
        "description": "DocLayNet: Document Layout Analysis (CDLA-Permissive)",
        "hf_repo": "ds4sd/DocLayNet",
        "url": "https://github.com/DS4SD/DocLayNet",
    },
    "pubtables_1m": {
        "description": "PubTables-1M: Scientific Table Structure Extraction (CDLA-Permissive)",
        "hf_repo": "bsmock/pubtables-1m",
        "url": "https://huggingface.co/datasets/bsmock/pubtables-1m",
    },
    "chartqa": {
        "description": "ChartQA: Chart Question Answering (Apache-2.0)",
        "hf_repo": "HuggingFaceM4/ChartQA",
        "url": "https://github.com/vis-nlp/ChartQA",
    },
    "chartqapro": {
        "description": "ChartQAPro: Harder Multi-turn Chart Reasoning",
        "hf_repo": "vis-nlp/ChartQAPro",
        "url": "https://github.com/vis-nlp/ChartQAPro",
    },
    "sciq": {
        "description": "SciQ: Science Exam QA (CC BY-NC 3.0)",
        "hf_repo": "allenai/sciq",
        "url": "https://huggingface.co/datasets/allenai/sciq",
    },
}


def download_benchmark(benchmark_name: str, target_dir: Path, split: Optional[str] = None):
    if benchmark_name not in BENCHMARK_RESOURCES:
        raise ValueError(f"Unknown benchmark: {benchmark_name}. Supported: {list(BENCHMARK_RESOURCES.keys())}")

    info = BENCHMARK_RESOURCES[benchmark_name]
    logger.info(f"Downloading benchmark '{benchmark_name}' ({info['description']})...")
    dest = target_dir / benchmark_name
    dest.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset
        logger.info(f"Using Hugging Face Datasets to stream/cache: {info['hf_repo']}")
        dataset = load_dataset(info["hf_repo"], split=split)
        logger.info(f"Successfully loaded {benchmark_name} ({split or 'all splits'}).")
    except ImportError:
        logger.warning(
            f"The 'datasets' library is not installed locally. "
            f"Please run `pip install datasets` or run the notebook on Kaggle/Colab with GPU acceleration. "
            f"Official repo: {info['url']}"
        )


def main():
    parser = argparse.ArgumentParser(description="Download Benchmark Datasets")
    parser.add_argument("--benchmark", type=str, choices=list(BENCHMARK_RESOURCES.keys()) + ["all"], default="all")
    parser.add_argument("--output-dir", type=str, default="data/evaluation/public")
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    if args.benchmark == "all":
        for b in BENCHMARK_RESOURCES:
            download_benchmark(b, out_path)
    else:
        download_benchmark(args.benchmark, out_path)


if __name__ == "__main__":
    main()
