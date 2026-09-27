from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.synthetic_dataset.schemas import SyntheticProgramExample

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output" / "pdf" / "synthetic_programs_v1"


def _footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#4F46E5"))
    canvas.drawCentredString(A4[0] / 2, 10 * mm, "DOCUMENT SYNTHÉTIQUE DE TEST")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, f"Page {document.page}")
    canvas.restoreState()


def create_program_pdf(example: SyntheticProgramExample, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "SyntheticTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#172554"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "SyntheticBanner",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.white,
            backColor=colors.HexColor("#4F46E5"),
            borderPadding=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "SyntheticHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#312E81"),
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    body = ParagraphStyle(
        "SyntheticBody",
        parent=styles["BodyText"],
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor("#1E293B"),
    )
    small = ParagraphStyle(
        "SyntheticSmall",
        parent=body,
        fontSize=7.2,
        leading=9,
    )
    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title=f"Aperçu synthétique {example.id}",
        author="TrainFlow AI - données synthétiques",
    )
    story = [
        Paragraph("DOCUMENT SYNTHÉTIQUE DE TEST", styles["SyntheticBanner"]),
        Spacer(1, 5 * mm),
        Paragraph(escape(example.output.title), styles["SyntheticTitle"]),
    ]
    summary = [
        [
            Paragraph("Thème", small),
            Paragraph(escape(example.input.theme), body),
            Paragraph("Niveau", small),
            Paragraph(escape(example.input.level.value), body),
        ],
        [
            Paragraph("Public cible", small),
            Paragraph(escape(example.input.target_audience), body),
            Paragraph("Modalité", small),
            Paragraph(escape(example.input.delivery_mode.value), body),
        ],
        [
            Paragraph("Durée", small),
            Paragraph(f"{example.input.total_duration_minutes // 60} h", body),
            Paragraph("Jours", small),
            Paragraph(str(example.input.planned_days_count), body),
        ],
    ]
    table = Table(summary, colWidths=[25 * mm, 68 * mm, 22 * mm, 52 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#EEF2FF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            table,
            Paragraph("Objectif général", styles["SyntheticHeading"]),
            Paragraph(escape(example.output.general_objective), body),
            Paragraph("Objectifs pédagogiques", styles["SyntheticHeading"]),
            Paragraph(
                "<br/>".join(
                    f"• {escape(value)}" for value in example.output.pedagogical_objectives
                ),
                body,
            ),
            Paragraph("Prérequis", styles["SyntheticHeading"]),
            Paragraph(
                "<br/>".join(f"• {escape(value)}" for value in example.output.prerequisites), body
            ),
            Paragraph("Programme détaillé", styles["SyntheticHeading"]),
        ]
    )
    for day in example.output.days:
        module_rows = [
            [
                Paragraph("Module", small),
                Paragraph("Concepts et objectif", small),
                Paragraph("Méthodes / moyens", small),
                Paragraph("Type", small),
                Paragraph("Durée", small),
            ]
        ]
        for module in day.modules:
            module_rows.append(
                [
                    Paragraph(
                        f"<b>{escape(module.title)}</b><br/>{escape(module.description)}", small
                    ),
                    Paragraph(
                        "<br/>".join(f"• {escape(value)}" for value in module.concepts)
                        + f"<br/><i>{escape(module.pedagogical_objective)}</i>",
                        small,
                    ),
                    Paragraph(
                        "<br/>".join(
                            f"• {escape(value)}"
                            for value in [
                                *module.pedagogical_methods,
                                *module.pedagogical_resources,
                                *module.activities,
                            ]
                        ),
                        small,
                    ),
                    Paragraph(escape(module.module_type.value), small),
                    Paragraph(f"{module.duration_minutes} min", small),
                ]
            )
        day_table = Table(
            module_rows, colWidths=[39 * mm, 54 * mm, 42 * mm, 20 * mm, 18 * mm], repeatRows=1
        )
        day_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0E7FF")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#94A3B8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(
            KeepTogether(
                [
                    Paragraph(
                        f"Jour {day.day_number} - {escape(day.title)}", styles["SyntheticHeading"]
                    ),
                    Paragraph(escape(day.objective), body),
                    *(
                        [
                            Paragraph(
                                "<b>Fonction pédagogique :</b> "
                                + escape(day.pedagogical_function),
                                small,
                            )
                        ]
                        if day.pedagogical_function
                        else []
                    ),
                    Spacer(1, 2 * mm),
                    day_table,
                ]
            )
        )
    story.extend(
        [
            Paragraph("Méthodes et évaluation", styles["SyntheticHeading"]),
            Paragraph(
                f"<b>Méthodes :</b> {escape(', '.join(example.output.teaching_methods))}<br/>"
                f"<b>Moyens :</b> {escape(', '.join(example.output.pedagogical_resources))}<br/>"
                f"<b>Évaluation :</b> {escape(example.output.evaluation_method)}",
                body,
            ),
            Spacer(1, 4 * mm),
            Paragraph(
                "Ce document est un aperçu généré à partir de données entièrement synthétiques. "
                "Il ne constitue ni une autorisation, ni une certification, "
                "ni un document contractuel.",
                small,
            ),
        ]
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path


def generate_pdf_previews(
    examples: list[SyntheticProgramExample], output_dir: Path = OUTPUT_DIR
) -> list[Path]:
    return [
        create_program_pdf(example, output_dir / f"{example.id}.pdf") for example in examples[:10]
    ]
