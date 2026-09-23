from __future__ import annotations

from copy import deepcopy
from io import BytesIO

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from app.documents.program_pdf import generate_program_pdf
from app.schemas.program_document import (
    ProgramContent,
    ProgramTrainer,
    TrainerProfile,
    TrainingLevel,
    TrainingProgramDay,
    TrainingProgramInput,
    TrainingProgramOutput,
)


def make_program(day_count: int = 3, *, long: bool = False) -> TrainingProgramOutput:
    minutes = 420
    days = []
    for index in range(1, day_count + 1):
        concepts = ["Analyse des besoins", "Mise en œuvre guidée"]
        if long:
            concepts += [
                f"Concept détaillé numéro {value} avec accents : évaluation, qualité"
                for value in range(12)
            ]
        days.append(
            TrainingProgramDay(
                day_number=index,
                title=f"Étape pédagogique {index}",
                contents=[
                    ProgramContent(title=f"Module {index}.{module}", concepts=concepts)
                    for module in range(1, 4)
                ],
                methods_and_resources=["Étude de cas", "Exercice pratique", "Support numérique"],
                theory_minutes=180,
                practice_minutes=240,
            )
        )
    total = day_count * minutes
    return TrainingProgramOutput(
        theme="Management avancé et amélioration continue",
        target_audience="Responsables d’équipe",
        training_objectives=["Piloter une démarche structurée"],
        pedagogical_objectives=["Analyser une situation", "Construire une réponse adaptée"],
        trainer=ProgramTrainer(name="Élodie Noël", hours=total / 60),
        days=days,
        total_duration_minutes=total,
        evaluation_method="Étude de cas finale et grille critériée.",
    )


@pytest.mark.parametrize("day_count", [1, 3, 5])
def test_pdf_is_valid_for_supported_day_counts(day_count: int) -> None:
    content = generate_program_pdf(make_program(day_count))
    assert content.startswith(b"%PDF")
    assert len(PdfReader(BytesIO(content)).pages) >= 1


def test_pdf_preserves_accents_and_long_content() -> None:
    content = generate_program_pdf(make_program(5, long=True))
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    assert "Élodie Noël" in text
    assert "Concept détaillé" in text
    assert "PrestaCode" in text


def test_renderer_does_not_mutate_program() -> None:
    program = make_program()
    before = deepcopy(program.model_dump())
    generate_program_pdf(program)
    assert program.model_dump() == before


def test_duration_and_trainer_totals_are_enforced() -> None:
    payload = make_program().model_dump()
    payload["total_duration_minutes"] += 1
    with pytest.raises(ValidationError):
        TrainingProgramOutput.model_validate(payload)


def test_program_validates_against_business_input() -> None:
    program = make_program()
    source = TrainingProgramInput(
        training_name=program.theme,
        client_need="Structurer les pratiques de management.",
        target_audience=program.target_audience,
        level=TrainingLevel.ADVANCED,
        total_duration_minutes=program.total_duration_minutes,
        planned_days_count=len(program.days),
        delivery_mode="Présentiel",
        location="Tunis",
        trainer_profile=TrainerProfile(
            name=program.trainer.name, specialties=["Management"], years_of_experience=12
        ),
    )
    program.validate_against(source)


@pytest.mark.parametrize(
    ("theme", "module", "concept"),
    [
        ("Cybersécurité", "Phishing et ingénierie sociale", "Liens suspects"),
        ("Excel", "Tableaux croisés dynamiques", "Champs calculés"),
        ("Management", "Conduite d’équipe", "Feedback situationnel"),
    ],
)
def test_pdf_keeps_the_same_structure_with_dynamic_business_content(
    theme: str, module: str, concept: str
) -> None:
    program = make_program(1).model_copy(
        update={
            "theme": theme,
            "days": [
                TrainingProgramDay(
                    day_number=1,
                    title=f"Journée {theme}",
                    contents=[ProgramContent(title=module, concepts=[concept, "Exercice guidé"])],
                    methods_and_resources=["Présentation interactive", "Étude de cas"],
                    theory_minutes=180,
                    practice_minutes=240,
                )
            ],
            "total_duration_minutes": 420,
            "trainer": ProgramTrainer(name="Élodie Noël", hours=7),
        }
    )

    reader = PdfReader(BytesIO(generate_program_pdf(program)))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert theme in text
    assert module in text
    assert concept in text
    assert "Contenus / concepts clés à aborder" in text
    assert "Méthodes, moyens" in text
    assert "pédagogiques et" in text
    assert "équipements" in text
