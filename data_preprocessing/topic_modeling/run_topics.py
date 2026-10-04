#!/usr/bin/env python3
"""CLI: BERTopic per journey × satisfaction + Gemini category naming.

Examples:
    python -m topic_modeling.run_topics
    python -m topic_modeling.run_topics --input processed_data/reviews_processed.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from config import DEFAULT_PROCESSED_DIR, DEFAULT_OUTPUT_FILENAME, TOPIC_OUTPUT_JSON
from topic_modeling.bertopic_topics import TopicModelingError, run_topic_modeling


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run BERTopic per journey×satisfaction and name topics with Gemini."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_PROCESSED_DIR / DEFAULT_OUTPUT_FILENAME,
        help="CSV with review + journey *_pred columns.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=TOPIC_OUTPUT_JSON,
        help="Output JSON path for topics_by_journey.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger = logging.getLogger("run_topics")

    input_csv = args.input
    if not input_csv.is_absolute():
        input_csv = (Path.cwd() / input_csv).resolve()
    output_json = args.output
    if not output_json.is_absolute():
        output_json = (Path.cwd() / output_json).resolve()

    if not input_csv.exists():
        logger.error(
            "Input not found: %s. Run the main pipeline first or pass --input.",
            input_csv,
        )
        return 1

    logger.info("Loading %s", input_csv)
    df = pd.read_csv(input_csv)
    try:
        payload = run_topic_modeling(df, output_json=output_json)
    except TopicModelingError as exc:
        logger.error("%s", exc)
        return 1
    except Exception:
        logger.exception("Topic modeling failed.")
        return 1

    for journey, block in payload.get("journeys", {}).items():
        by_sat = block.get("by_satisfaction") or {}
        for sat, sat_block in by_sat.items():
            logger.info(
                "Journey %-12s %-8s docs=%s topics=%s skipped=%s",
                journey,
                sat,
                sat_block.get("document_count"),
                len(sat_block.get("topics", [])),
                sat_block.get("skipped", False),
            )
        if not by_sat:
            logger.info(
                "Journey %-12s docs=%s topics=%s",
                journey,
                block.get("document_count"),
                len(block.get("topics", [])),
            )
    logger.info("Done. JSON: %s", output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
