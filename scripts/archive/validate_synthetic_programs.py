from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.validation import load_jsonl, validate_collection  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Valider un dataset JSONL synthétique.")
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    result = validate_collection(load_jsonl(args.dataset))
    print(f"Dataset valide: {result['valid_examples']} exemples")
    print(f"Doublons exacts: {result['exact_duplicates']}")
    print(f"Quasi-doublons signalés: {result['quasi_duplicates']}")


if __name__ == "__main__":
    main()
