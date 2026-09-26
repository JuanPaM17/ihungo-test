from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sentiment_analysis.processor import ExcelSentimentProcessor
from sentiment_analysis.providers.paralleldots import ParallelDotsProvider


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentiment-analysis",
        description="Analyze sentiment of Excel text cells using ParallelDots.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        metavar="FILE",
        help="Path to the input Excel file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        metavar="FILE",
        help="Path for the output Excel file.",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        metavar="NAME",
        help="Sheet name to process (default: active sheet).",
    )
    parser.add_argument(
        "--column",
        default=3,
        type=int,
        metavar="N",
        help="1-based column index containing the text to analyze (default: 3).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        provider = ParallelDotsProvider()
    except EnvironmentError as exc:
        logging.error("%s", exc)
        return 1

    processor = ExcelSentimentProcessor(provider=provider)

    try:
        processor.process(
            input_path=args.input,
            output_path=args.output,
            sheet_name=args.sheet,
            text_column=args.column,
        )
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1
    except Exception as exc:
        logging.error("Unexpected error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
