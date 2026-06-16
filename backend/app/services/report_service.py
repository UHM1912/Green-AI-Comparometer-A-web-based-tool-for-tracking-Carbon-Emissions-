import io
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_report(job: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    story = []
    getSampleStyleSheet()

    c_primary = colors.HexColor("#6E887B")
    c_secondary = colors.HexColor("#A7BEB1")
    c_neutral_dark = colors.HexColor("#2C3531")
    c_neutral_light = colors.HexColor("#F1F5F2")

    title_style = ParagraphStyle(
        name="ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=c_primary,
        alignment=TA_CENTER,
        spaceAfter=25,
    )
    heading_style = ParagraphStyle(
        name="SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        name="CustomBody",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_neutral_dark,
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        name="BulletBody",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_neutral_dark,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5,
    )
    code_header_style = ParagraphStyle(
        name="CodeHeader",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    table_header_style = ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    table_cell_style = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=9,
        alignment=TA_CENTER,
    )

    co2_saved = job["original_co2"] - job["optimized_co2"]
    co2_pct = (co2_saved / job["original_co2"] * 100) if job["original_co2"] > 0 else 0
    power_saved = job["original_power"] - job["optimized_power"]
    power_pct = (power_saved / job["original_power"] * 100) if job["original_power"] > 0 else 0
    duration_saved = job["original_duration"] - job["optimized_duration"]
    duration_pct = (duration_saved / job["original_duration"] * 100) if job["original_duration"] > 0 else 0

    story.append(Paragraph("EcoRefactor Optimization Report", title_style))
    story.append(Spacer(1, 15))

    meta_table = Table(
        [
            [Paragraph("<b>File Analyzed:</b>", body_style), Paragraph(job["filename"], body_style)],
            [Paragraph("<b>Date Generated:</b>", body_style), Paragraph(job["timestamp"], body_style)],
        ],
        colWidths=[110, 380],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, c_secondary),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Executive Summary", heading_style))
    story.append(
        Paragraph(
            (
                "This report compares the original and optimized code paths using benchmark-oriented execution data. "
                "The focus is practical efficiency: runtime, compute effort, and energy proxy signals."
            ),
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Comparative Performance Metrics", heading_style))
    metrics_table = Table(
        [
            [
                Paragraph("<b>Metric</b>", table_header_style),
                Paragraph("<b>Original Code</b>", table_header_style),
                Paragraph("<b>Optimized Code</b>", table_header_style),
                Paragraph("<b>Savings (%)</b>", table_header_style),
            ],
            [
                Paragraph("CO2 Emissions", table_cell_style),
                Paragraph(f"{job['original_co2']:.6f} kg", table_cell_style),
                Paragraph(f"{job['optimized_co2']:.6f} kg", table_cell_style),
                Paragraph(f"<b>{co2_pct:.1f}%</b>", table_cell_style),
            ],
            [
                Paragraph("Energy Consumed", table_cell_style),
                Paragraph(f"{job['original_power']:.6f} kWh", table_cell_style),
                Paragraph(f"{job['optimized_power']:.6f} kWh", table_cell_style),
                Paragraph(f"<b>{power_pct:.1f}%</b>", table_cell_style),
            ],
            [
                Paragraph("Median Runtime", table_cell_style),
                Paragraph(f"{job['original_duration']:.4f} s", table_cell_style),
                Paragraph(f"{job['optimized_duration']:.4f} s", table_cell_style),
                Paragraph(f"<b>{duration_pct:.1f}%</b>", table_cell_style),
            ],
        ],
        colWidths=[140, 120, 120, 110],
    )
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_secondary),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_neutral_light]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(metrics_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Impact Interpretation", heading_style))
    story.append(
        Paragraph(
            (
                f"The optimized code saved {co2_saved:.5f} kg CO2 proxy, {power_saved:.6f} kWh, "
                f"and {duration_saved:.4f} seconds per measured run set."
            ),
            body_style,
        )
    )
    story.append(Paragraph(f"- LED bulb equivalent: {co2_saved * 500.0:.2f} hours", bullet_style))
    story.append(Paragraph(f"- Smartphone charges equivalent: {co2_saved * 120.0:.1f}", bullet_style))
    story.append(
        Paragraph(
            f"- Typical driving emissions avoided: {co2_saved * 2.5:.2f} kilometers",
            bullet_style,
        )
    )
    story.append(Spacer(1, 15))

    story.append(Paragraph("Optimization Actions Taken", heading_style))
    try:
        explanations = json.loads(job["explanations"])
    except Exception:
        explanations = [job["explanations"]]

    for index, explanation in enumerate(explanations, start=1):
        story.append(Paragraph(f"<b>{index}.</b> {explanation}", bullet_style))

    story.append(Spacer(1, 20))
    story.append(PageBreak())
    story.append(Paragraph("Code Structure Comparison", heading_style))
    story.append(Spacer(1, 5))

    original_lines = job["original_code"].split("\n")[:30]
    optimized_lines = job["optimized_code"].split("\n")[:30]
    original_snippet = "\n".join(original_lines)
    optimized_snippet = "\n".join(optimized_lines)

    if len(job["original_code"].split("\n")) > 30:
        original_snippet += "\n... (truncated)"
    if len(job["optimized_code"].split("\n")) > 30:
        optimized_snippet += "\n... (truncated)"

    code_cell_style = ParagraphStyle(
        name="CodeCell",
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=c_neutral_dark,
    )

    code_table = Table(
        [
            [
                Paragraph("Original Code", code_header_style),
                Paragraph("Optimized Code", code_header_style),
            ],
            [
                Paragraph(original_snippet.replace(" ", "&nbsp;").replace("\n", "<br/>"), code_cell_style),
                Paragraph(optimized_snippet.replace(" ", "&nbsp;").replace("\n", "<br/>"), code_cell_style),
            ],
        ],
        colWidths=[245, 245],
    )
    code_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("BACKGROUND", (0, 1), (-1, 1), c_neutral_light),
                ("GRID", (0, 0), (-1, -1), 0.5, c_secondary),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(code_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
