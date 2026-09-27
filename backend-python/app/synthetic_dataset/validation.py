from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable
from difflib import SequenceMatcher
from pathlib import Path

from pydantic import ValidationError

from app.synthetic_dataset.schemas import SyntheticProgramExample

FORBIDDEN_PATTERNS = (
    r"\bsignature\b",
    r"\bcachet\b",
    r"n[°º]?\s*(?:d['’])?enregistrement",
    r"\bréférence officielle\b",
    r"\bautorisation officielle\b",
)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d ()/.-]{7,}\d)(?!\w)")


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def fingerprint(example: SyntheticProgramExample) -> str:
    parts = [
        example.input.theme,
        example.input.target_audience,
        str(example.input.total_duration_minutes),
        *(day.title for day in example.output.days),
        *(module.title for day in example.output.days for module in day.modules),
    ]
    return hashlib.sha256("|".join(normalized_text(part) for part in parts).encode()).hexdigest()


def similarity_text(example: SyntheticProgramExample) -> str:
    parts = [example.input.theme, example.input.target_audience]
    parts.extend(day.title for day in example.output.days)
    parts.extend(module.title for day in example.output.days for module in day.modules)
    return normalized_text(" ".join(parts))


class DuplicateRegistry:
    def __init__(self, quasi_threshold: float = 0.88) -> None:
        self.quasi_threshold = quasi_threshold
        self._fingerprints: set[str] = set()
        self._texts: list[tuple[str, str]] = []

    def inspect(self, example: SyntheticProgramExample) -> tuple[bool, list[tuple[str, float]]]:
        digest = fingerprint(example)
        exact = digest in self._fingerprints
        candidate = similarity_text(example)
        quasi = [
            (example_id, score)
            for example_id, previous in self._texts
            if (score := SequenceMatcher(None, candidate, previous).ratio()) >= self.quasi_threshold
        ]
        return exact, sorted(quasi, key=lambda item: item[1], reverse=True)

    def add(self, example: SyntheticProgramExample) -> None:
        self._fingerprints.add(fingerprint(example))
        self._texts.append((example.id, similarity_text(example)))


def validate_safe_content(example: SyntheticProgramExample) -> None:
    serialized = json.dumps(example.model_dump(mode="json"), ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, serialized, flags=re.IGNORECASE):
            raise ValueError(f"Contenu officiel ou interdit détecté: {pattern}")
    if EMAIL_PATTERN.search(serialized) or PHONE_PATTERN.search(serialized):
        raise ValueError("Une donnée personnelle potentielle a été détectée.")


def load_jsonl(path: Path) -> list[SyntheticProgramExample]:
    examples: list[SyntheticProgramExample] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                examples.append(SyntheticProgramExample.model_validate_json(line))
            except ValidationError as exc:
                raise ValueError(f"Ligne {line_number} invalide: {exc}") from exc
    return examples


def validate_collection(examples: Iterable[SyntheticProgramExample]) -> dict[str, int]:
    registry = DuplicateRegistry()
    count = exact_duplicates = quasi_duplicates = 0
    for example in examples:
        validate_safe_content(example)
        exact, quasi = registry.inspect(example)
        if exact:
            exact_duplicates += 1
            raise ValueError(f"Doublon exact détecté: {example.id}")
        quasi_duplicates += len(quasi)
        registry.add(example)
        count += 1
    return {
        "valid_examples": count,
        "exact_duplicates": exact_duplicates,
        "quasi_duplicates": quasi_duplicates,
    }
