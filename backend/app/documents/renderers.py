from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLUE = colors.HexColor("#1d4ed8")


def render_document(document_type: str, data: dict[str, Any]) -> bytes:
    renderer = {
        "PROGRAM": _program,
        "QUOTE": _quote,
        "AGREEMENT": _agreement,
        "ATTENDANCE_SHEET": _attendance,
        "CERTIFICATE": _certificate,
    }[document_type]
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=data["display_name"],
    )
    document.build(renderer(data), onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], textColor=BLUE))
    styles.add(ParagraphStyle(name="Centered", parent=styles["BodyText"], alignment=TA_CENTER))
    return styles


def _heading(title: str, data: dict[str, Any]) -> list:
    styles = _styles()
    return [
        Paragraph(title, styles["DocTitle"]),
        Paragraph(f"Référence : {data['case']['reference']}", styles["Normal"]),
        Paragraph(f"Généré le : {data['generated_on']}", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]


def _program(data):
    styles = _styles()
    story = _heading("Programme de formation", data)
    program = data["program"]
    story += [
        Paragraph(program["title"], styles["Heading2"]),
        Paragraph(f"Entreprise : {data['company']['name']}", styles["Normal"]),
        Paragraph(f"Formateur : {data['trainer']['full_name']}", styles["Normal"]),
        Paragraph(f"Durée totale : {program['duration']}", styles["Normal"]),
        Paragraph(
            f"Théorie : {program['theory']} — Pratique : {program['practice']}",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Objectifs", styles["Heading2"]),
        Paragraph(program["objectives"] or "Non renseignés", styles["BodyText"]),
        Paragraph("Prérequis", styles["Heading2"]),
        Paragraph(program["prerequisites"] or "Aucun prérequis particulier.", styles["BodyText"]),
    ]
    for day in program["days"]:
        story += [Spacer(1, 4 * mm), Paragraph(day["title"], styles["Heading2"])]
        for module in day["modules"]:
            story.append(
                Paragraph(
                    f"{module['position']}. {module['title']} — {module['duration']}",
                    styles["Heading3"],
                )
            )
            if module["content"]:
                story.append(Paragraph(module["content"], styles["BodyText"]))
            for child in module["submodules"]:
                story.append(
                    Paragraph(
                        f"• {child['title']} — {child['duration']}",
                        styles["BodyText"],
                    )
                )
    return story


def _quote(data):
    styles = _styles()
    pricing = data["pricing"]
    story = _heading("Devis", data)
    story += [
        Paragraph(f"Entreprise cliente : {data['company']['name']}", styles["Normal"]),
        Paragraph(f"Contact : {data['contact']['full_name']}", styles["Normal"]),
        Paragraph(f"Formation : {data['case']['theme']}", styles["Normal"]),
        Paragraph(data["case"]["description"] or "", styles["BodyText"]),
        Spacer(1, 5 * mm),
        Table(
            [
                ["Durée", data["program"]["duration"]],
                ["Nombre de journées", str(data["program"]["day_count"])],
                ["Participants", str(data["need"]["participant_count"] or "Non renseigné")],
                ["Formateur", data["trainer"]["full_name"]],
                ["Montant HT", pricing["total_excluding_tax"]],
                ["TVA", pricing["vat_rate"]],
                ["Montant TVA", pricing["vat_amount"]],
                ["Total TTC", pricing["total_including_tax"]],
            ],
            colWidths=[65 * mm, 95 * mm],
            style=_table_style(),
        ),
    ]
    if pricing["vat_note"]:
        story += [Spacer(1, 4 * mm), Paragraph(pricing["vat_note"], styles["BodyText"])]
    return story


def _agreement(data):
    styles = _styles()
    p = data["pricing"]
    return _heading("Convention de formation", data) + [
        Paragraph("Parties", styles["Heading2"]),
        Paragraph(
            f"La présente convention est établie avec {data['company']['name']}.",
            styles["BodyText"],
        ),
        Paragraph("Objet", styles["Heading2"]),
        Paragraph(
            f"Organisation de la formation « {data['case']['theme']} ».",
            styles["BodyText"],
        ),
        Paragraph("Conditions", styles["Heading2"]),
        Paragraph(
            f"Durée : {data['program']['duration']} — Formateur : "
            f"{data['trainer']['full_name']} — Lieu : {data['need']['location'] or 'à définir'}.",
            styles["BodyText"],
        ),
        Paragraph(
            f"Prix : {p['total_excluding_tax']} HT, TVA {p['vat_rate']}, "
            f"soit {p['total_including_tax']} TTC.",
            styles["BodyText"],
        ),
        Spacer(1, 20 * mm),
        Table(
            [
                ["Pour l’organisme de formation", "Pour l’entreprise cliente"],
                ["Signature :", "Signature :"],
            ],
            colWidths=[80 * mm, 80 * mm],
            rowHeights=[10 * mm, 25 * mm],
            style=_table_style(),
        ),
    ]


def _attendance(data):
    styles = _styles()
    story = _heading("Feuille de présence", data) + [
        Paragraph(f"Formation : {data['case']['theme']}", styles["Normal"]),
        Paragraph(f"Entreprise : {data['company']['name']}", styles["Normal"]),
        Paragraph(f"Formateur : {data['trainer']['full_name']}", styles["Normal"]),
        Spacer(1, 5 * mm),
    ]
    rows = [["Nom et prénom", "Matin", "Après-midi", "Signature"]]
    rows += [["", "", "", ""] for _ in range(max(data["need"]["participant_count"] or 8, 8))]
    for index, day in enumerate(data["program"]["days"]):
        if index:
            story.append(PageBreak())
        story += [
            Paragraph(day["title"], styles["Heading2"]),
            Table(
                rows,
                colWidths=[65 * mm, 28 * mm, 32 * mm, 38 * mm],
                rowHeights=10 * mm,
                repeatRows=1,
                style=_table_style(),
            ),
        ]
    return story


def _certificate(data):
    styles = _styles()
    return _heading("Attestation collective de formation", data) + [
        Spacer(1, 12 * mm),
        Paragraph(
            f"Il est attesté que la formation « {data['case']['theme']} » a été préparée "
            f"pour l’entreprise {data['company']['name']}.",
            styles["Centered"],
        ),
        Spacer(1, 6 * mm),
        Paragraph(
            f"Formateur : {data['trainer']['full_name']}<br/>"
            f"Durée : {data['program']['duration']}<br/>"
            f"Participants prévus : {data['need']['participant_count'] or 'Non renseigné'}<br/>"
            f"Période : {data['need']['period']}",
            styles["Centered"],
        ),
        Spacer(1, 8 * mm),
        Paragraph(
            "Document collectif préparatoire : aucune identité individuelle de participant "
            "n’est enregistrée.",
            styles["Centered"],
        ),
    ]


def _table_style():
    return TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]
    )


def _footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(18 * mm, 10 * mm, "Gestion Formations — Document généré localement")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {document.page}")
    canvas.restoreState()
