from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.generator import (  # noqa: E402
    DURATIONS,
    STYLES,
    THEMES,
    generate_dataset,
    write_quality_report,
)


def csv_values(value: str | None, default: list) -> list:
    if not value:
        return default
    requested = {item.strip().casefold() for item in value.split(",") if item.strip()}
    return [item for item in default if str(getattr(item, "value", item)).casefold() in requested]


def main() -> None:
    parser = argparse.ArgumentParser(description="Générer le dataset synthétique de programmes.")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--themes")
    parser.add_argument("--styles")
    parser.add_argument("--durations")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data" / "training_programs_synthetic_v1.jsonl"
    )
    parser.add_argument("--seed", type=int, default=20260804)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--generate-pdf-previews", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count doit être supérieur à zéro")
    themes = csv_values(args.themes, THEMES)
    styles = csv_values(args.styles, STYLES)
    durations = [int(value) for value in args.durations.split(",")] if args.durations else DURATIONS
    if not themes or not styles or not durations:
        parser.error("Les filtres ne correspondent à aucune valeur prise en charge.")
    # Filters are applied to the shared balanced schedules for reproducible generation.
    from app.synthetic_dataset import generator  # noqa: E402

    generator.STYLES = styles
    generator.DURATIONS = durations
    examples, stats, previews = generate_dataset(
        count=args.count,
        output=args.output,
        seed=args.seed,
        max_retries=args.max_retries,
        themes=themes,
        generate_previews=args.generate_pdf_previews,
    )
    report = ROOT / "reports" / "synthetic_dataset_v1_report.md"
    write_quality_report(examples, stats, report)
    print(f"Dataset JSONL: {args.output}")
    print(f"Dataset JSON: {args.output.with_suffix('.json')}")
    print(f"Rapport: {report}")
    print(f"PDF générés: {len(previews)}")


if __name__ == "__main__":
    main()
