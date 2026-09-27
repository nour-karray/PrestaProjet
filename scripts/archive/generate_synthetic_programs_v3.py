from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.review import migrate_family_ids  # noqa: E402
from app.synthetic_dataset.v3 import OllamaV3Client, regenerate_v3  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Régénérer pédagogiquement les programmes v3.")
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data" / "training_programs_synthetic_v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "training_programs_synthetic_v3.jsonl",
    )
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()
    archive = ROOT / "data" / "archive" / "training_programs_synthetic_v1_original.jsonl"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        shutil.copy2(args.source, archive)
    raw = [json.loads(line) for line in args.source.read_text(encoding="utf-8").splitlines()]
    originals = migrate_family_ids(raw)
    resume_examples = None
    if args.output.exists():
        partial = [
            json.loads(line)
            for line in args.output.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        resume_examples = migrate_family_ids(partial)
        print(f"Reprise de {len(resume_examples)} programmes déjà validés.", flush=True)
    client = OllamaV3Client(timeout_seconds=900)
    client.health()
    examples, stats, violations = regenerate_v3(
        originals,
        args.output,
        client,
        max_retries=args.max_retries,
        resume_examples=resume_examples,
    )
    summary = {
        "programs": len(examples),
        "violating_programs": len(violations),
        "regenerated": stats.regenerated,
        "qwen_calls": stats.calls,
        "rejected": stats.rejected,
        "retries": stats.retries,
        "elapsed_seconds": round(stats.elapsed_seconds, 2),
        "violation_details": violations,
        "errors": dict(stats.errors),
    }
    report = ROOT / "reports" / "synthetic_dataset_v3_generation_stats.json"
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
