#!/usr/bin/env python3
"""CLI entry point for the customer-review preprocessing pipeline.

Examples:
    python run_pipeline.py --input raw_data/combined_reviews.csv
    python run_pipeline.py --input raw_data/combined_reviews.csv --topics
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from cleaning.clean_reviews import MissingRawColumnsError
from config import (
    DEFAULT_INPUT_FILENAME,
    DEFAULT_OUTPUT_FILENAME,
    DEFAULT_PROCESSED_DIR,
    DEFAULT_RAW_DIR,
    PipelineConfig,
)
from journey_classification.classify import JourneyClassificationError
from pipeline import run_pipeline
from topic_modeling.bertopic_topics import TopicModelingError
from validation.validate import OutputFormatError


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preprocess second-hand car shop customer reviews: "
            "clean, label satisfaction, attach journey stages, optionally run BERTopic."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "Path to raw reviews CSV. Default: "
            f"{DEFAULT_RAW_DIR / DEFAULT_INPUT_FILENAME} "
            "(or REVIEW_RAW_CSV)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Path for processed CSV. Default: "
            f"{DEFAULT_PROCESSED_DIR / DEFAULT_OUTPUT_FILENAME} "
            "(or REVIEW_PROCESSED_CSV)."
        ),
    )
    parser.add_argument(
        "--topics",
        action="store_true",
        help=(
            "After processing, run BERTopic per journey and name topics with Gemini "
            "(requires requirements-topics.txt + .env GEMINI_API_KEY)."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger = logging.getLogger("run_pipeline")

    config = PipelineConfig.from_sources(
        input_csv=args.input,
        output_csv=args.output,
        run_topics=args.topics,
    )
    logger.info("Input CSV:  %s", config.input_csv)
    logger.info("Output CSV: %s", config.output_csv)
    logger.info("Run topics: %s", config.run_topics)

    try:
        metrics = run_pipeline(config)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except (
        MissingRawColumnsError,
        OutputFormatError,
        JourneyClassificationError,
        TopicModelingError,
    ) as exc:
        logger.error("%s", exc)
        return 1
    except Exception:
        logger.exception("Pipeline failed unexpectedly.")
        return 1

    logger.info(
        "Done. final=%s positive=%s negative=%s stores=%s",
        metrics.final_row_count,
        metrics.positive_count,
        metrics.negative_count,
        metrics.unique_store_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
