from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.documents.program_pdf import generate_program_pdf
from app.schemas.program_document import TrainingProgramOutput

ROOT = Path(__file__).resolve().parents[3]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_migrated_dataset_has_120_unique_valid_programs() -> None:
    rows = load_jsonl(ROOT / "data/training_programs_final.jsonl")
    assert len(rows) == 120
    assert len({row["id"] for row in rows}) == 120
    for row in rows:
        program = TrainingProgramOutput.model_validate(row["output"])
        assert len(program.days) == row["input"]["planned_days_count"]
        assert program.total_duration_minutes == row["input"]["total_duration_minutes"]
        assert all(day.contents for day in program.days)
        assert all(day.theory_minutes > 0 for day in program.days)
        assert all(day.practice_minutes > 0 for day in program.days)
        assert all(day.theory_minutes + day.practice_minutes > 0 for day in program.days)


def test_migration_preserves_source_business_keys() -> None:
    source = load_jsonl(ROOT / "data/training_programs_clean.jsonl")
    final = load_jsonl(ROOT / "data/training_programs_final.jsonl")
    for before, after in zip(source, final, strict=True):
        assert before["id"] == after["id"]
        assert before["generation_family_id"] == after["generation_family_id"]
        for key in (
            "theme",
            "sector",
            "target_audience",
            "level",
            "total_duration_minutes",
            "planned_days_count",
        ):
            assert before["input"][key] == after["input"][key]
        assert after["metadata"]["final_migration"]["migrated"] is True


def test_representative_levels_render_as_complete_pdfs() -> None:
    rows = load_jsonl(ROOT / "data/training_programs_final.jsonl")
    for level in ("beginner", "intermediate", "advanced", "expert"):
        row = next(item for item in rows if item["input"]["level"] == level)
        program = TrainingProgramOutput.model_validate(row["output"])
        content = generate_program_pdf(program)
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert content.startswith(b"%PDF")
        assert all(f"J{day.day_number}" in text for day in program.days)
