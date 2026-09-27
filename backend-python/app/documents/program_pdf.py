from __future__ import annotations

import re
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.program_document import (
    ProgramContent,
    ProgramTrainer,
    TrainingProgramDay,
    TrainingProgramOutput,
)

NAVY = colors.HexColor("#172554")
BLUE = colors.HexColor("#2563EB")
PALE = colors.HexColor("#EFF6FF")
BORDER = colors.HexColor("#94A3B8")

METHOD_LABELS = {
    "EXPOSE": "Exposé interactif",
    "DEMONSTRATION": "Démonstration",
    "EXERCICE_PRATIQUE": "Exercice pratique",
    "ETUDE_DE_CAS": "Étude de cas",
    "MISE_EN_SITUATION": "Mise en situation",
    "ECHANGE_COLLECTIF": "Échange collectif",
    "EVALUATION": "Évaluation",
}


def _minutes(value: int) -> str:
    hours, minutes = divmod(value, 60)
    return f"{hours} h {minutes:02d}" if minutes else f"{hours} h"


def _footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(14 * mm, 12 * mm, A4[0] - 14 * mm, 12 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(NAVY)
    canvas.drawString(14 * mm, 8 * mm, "TrainFlow AI — Programme de formation")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(A4[0] - 14 * mm, 8 * mm, f"Page {document.page}")
    canvas.restoreState()


def generate_program_pdf(program: TrainingProgramOutput) -> bytes:
    """Render a validated program; the renderer never calls an LLM or mutates input."""
    validated = TrainingProgramOutput.model_validate(program)
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ProgramTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=NAVY,
        spaceAfter=7,
    )
    section = ParagraphStyle(
        "ProgramSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=NAVY,
        spaceBefore=5,
        spaceAfter=3,
    )
    body = ParagraphStyle(
        "ProgramBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
    )
    small = ParagraphStyle("ProgramSmall", parent=body, fontSize=6.7, leading=8.2)
    label = ParagraphStyle("ProgramLabel", parent=small, fontName="Helvetica-Bold", textColor=NAVY)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=17 * mm,
        title=validated.theme,
        author="TrainFlow AI",
    )

    def bullets(values: list[str], style=body) -> Paragraph:  # type: ignore[no-untyped-def]
        return Paragraph("<br/>".join(f"• {escape(value)}" for value in values), style)

    theory = sum(day.theory_minutes for day in validated.days)
    practice = sum(day.practice_minutes for day in validated.days)
    story = [
        Paragraph("TRAINFLOW AI | PROGRAMME DE FORMATION", title),
        Table(
            [
                [
                    Paragraph("Thème", label),
                    Paragraph(escape(validated.theme), body),
                    Paragraph("Durée", label),
                    Paragraph(_minutes(validated.total_duration_minutes), body),
                ],
                [
                    Paragraph("Public cible", label),
                    Paragraph(escape(validated.target_audience), body),
                    Paragraph("Journées", label),
                    Paragraph(str(len(validated.days)), body),
                ],
                [
                    Paragraph("Formateur", label),
                    Paragraph(escape(validated.trainer.name), body),
                    Paragraph("Heures", label),
                    Paragraph(f"{validated.trainer.hours:g} h", body),
                ],
            ],
            colWidths=[24 * mm, 79 * mm, 22 * mm, 45 * mm],
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
                    ("BACKGROUND", (0, 0), (0, -1), PALE),
                    ("BACKGROUND", (2, 0), (2, -1), PALE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        ),
        Paragraph("Objectifs de formation", section),
        bullets(validated.training_objectives),
        Paragraph("Objectifs pédagogiques", section),
        bullets(validated.pedagogical_objectives),
        Spacer(1, 3 * mm),
    ]
    rows: list[list[object]] = [
        [
            Paragraph("Jour / module", label),
            Paragraph("Contenus / concepts clés à aborder", label),
            Paragraph("Méthodes, moyens pédagogiques et équipements", label),
            Paragraph("Durée théorique", label),
            Paragraph("Durée pratique", label),
        ]
    ]
    for day in validated.days:
        content = [f"<b>{escape(day.title)}</b>"]
        for item in day.contents:
            content.append(f"<b>{escape(item.title)}</b>")
            content.extend(f"• {escape(concept)}" for concept in item.concepts)
        rows.append(
            [
                Paragraph(f"J{day.day_number}", label),
                Paragraph("<br/>".join(content), small),
                bullets(day.methods_and_resources, small),
                Paragraph(_minutes(day.theory_minutes), small),
                Paragraph(_minutes(day.practice_minutes), small),
            ]
        )
    rows.append(
        [
            Paragraph("TOTAL", label),
            "",
            "",
            Paragraph(_minutes(theory), label),
            Paragraph(_minutes(practice), label),
        ]
    )
    program_table = LongTable(
        rows,
        colWidths=[12 * mm, 82 * mm, 44 * mm, 18 * mm, 18 * mm],
        repeatRows=1,
        splitByRow=1,
    )
    program_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
                ("BACKGROUND", (0, -1), (-1, -1), PALE),
                ("SPAN", (0, -1), (2, -1)),
                ("ALIGN", (0, -1), (2, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.extend(
        [
            program_table,
            Paragraph("Méthode d’évaluation", section),
            Paragraph(escape(validated.evaluation_method), body),
            Spacer(1, 2 * mm),
            Paragraph("Document généré par TrainFlow AI, sans cachet ni signature.", small),
        ]
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def program_from_document_snapshot(data: dict[str, object]) -> TrainingProgramOutput:
    """Map the application snapshot to the sole PDF business contract."""
    raw_program = data["program"]
    raw_trainer = data["trainer"]
    raw_need = data["need"]
    assert isinstance(raw_program, dict)
    assert isinstance(raw_trainer, dict)
    assert isinstance(raw_need, dict)
    days = []
    for day_number, raw_day in enumerate(raw_program["days"], 1):
        contents = []
        for module in raw_day["modules"]:
            concepts = _concept_lines(module.get("content"))
            for child in module.get("submodules", []):
                concepts.append(child["title"])
                concepts.extend(_concept_lines(child.get("content")))
            contents.append(
                ProgramContent(title=module["title"], concepts=concepts or [module["title"]])
            )
        methods = [METHOD_LABELS.get(method, method) for method in raw_day.get("methods", [])]
        days.append(
            TrainingProgramDay(
                day_number=day_number,
                title=raw_day["title"],
                contents=contents,
                methods_and_resources=methods,
                theory_minutes=raw_day["theory_minutes"],
                practice_minutes=raw_day["practice_minutes"],
            )
        )
    total = sum(day.theory_minutes + day.practice_minutes for day in days)
    objectives = raw_program.get("objectives") or ""
    objective_lines = _concept_lines(objectives)
    pedagogical_lines = _concept_lines(raw_need.get("pedagogical_objectives"))
    return TrainingProgramOutput(
        theme=raw_program.get("theme") or raw_program["title"],
        target_audience=raw_need.get("target_audience") or "",
        training_objectives=objective_lines,
        pedagogical_objectives=pedagogical_lines,
        trainer=ProgramTrainer(name=raw_trainer["full_name"], hours=total / 60),
        days=days,
        total_duration_minutes=total,
        evaluation_method=raw_program.get("evaluation_method") or "",
    )


def _concept_lines(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [
        part.strip(" •-\t")
        for part in re.split(r"[\r\n;]+", value)
        if part.strip(" •-\t")
    ]
