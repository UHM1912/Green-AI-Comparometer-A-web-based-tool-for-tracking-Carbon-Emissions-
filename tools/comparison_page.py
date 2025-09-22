import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

results_file = Path("comparison_results.csv")

st.set_page_config(page_title="GreenAI Comparometer - Comparison", layout="wide")

# === Dark mode CSS styling with graph borders ===
st.markdown(
    """
    <style>
    /* Dark background with subtle texture */
    .stApp {
        background: linear-gradient(135deg, #121a13, #1b2b1e);
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        color: #a8d5a3;
        min-height: 100vh;
        position: relative;
    }
    [data-testid="stAppViewContainer"] > .main, .block-container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 1rem 2rem 2rem;
        position: relative;
        z-index: 10;
    }

    /* Title styling */
    .title-block {
        text-align: center;
        margin-bottom: 2rem;
    }
    .title-block h1 {
        margin: 0;
        font-size: 3rem;
        font-weight: 800;
        color: #6bdc6b;
        text-shadow: 0 0 8px #4ca64c;
    }
    .title-block p {
        font-size: 1.3rem;
        font-style: italic;
        color: #92c891;
        margin-top: 0.3rem;
        margin-bottom: 2rem;
    }

    /* Warning style for dark mode */
    .stWarning {
        background-color: #4d3c2f;
        border-left: 6px solid #bb8f42;
        color: #f3d88b;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }

    /* Dataframe styling */
    .stDataFrame > div {
        border-radius: 12px;
        box-shadow: 0 0 20px 1px rgba(107,220,107,0.4);
        overflow-x: auto;
        border: 1.5px solid #6bdc6b;
    }

    /* Separator line */
    hr {
        border: none;
        border-top: 1px solid #3e5a3e;
        margin: 2rem 0;
    }

    /* Hide Streamlit footer and menu */
    #MainMenu, footer {visibility: hidden;}

    /* Plotly graph container styling */
    .plotly-graph-div {
        border: 2.5px solid #4ca64c !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px 2px rgba(76,166,76,0.45);
        background: #182618 !important;
    }

    /* Plotly axis titles and ticks */
    .main-svg text, .main-svg .xtick text, .main-svg .ytick text {
        fill: #a8d5a3 !important;
        font-weight: 600 !important;
    }

    /* Plotly bar text styling */
    .main-svg .bar text {
        fill: #a8d5a3 !important;
        font-weight: 700 !important;
    }

    /* Responsive tweaks */
    @media (max-width: 1100px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title & subtitle
st.markdown(
    """
    <div class="title-block">
        <h1>📊 GreenAI Comparometer - Emissions Comparison</h1>
        <p>Compare results from <strong>eco2AI</strong>, <strong>CodeCarbon</strong>, and <strong>CarbonTracker</strong>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not results_file.exists():
    st.warning("⚠️ No results found. Please run at least one tracker first.")
    st.stop()

df = pd.read_csv(results_file)
df = pd.read_csv(results_file)

# If CarbonTracker columns exist, copy values into unified columns
if "energy_consumed_kwh" in df.columns:
    df["power_kwh"] = df["power_kwh"].fillna(df["energy_consumed_kwh"])
if "duration_seconds" in df.columns:
    df["duration_s"] = df["duration_s"].fillna(df["duration_seconds"])
df = df.drop(columns=["energy_consumed_kwh", "duration_seconds"], errors="ignore")


filenames = df["uploaded_filename"].unique().tolist()
selected_file = st.selectbox("Select file to compare:", filenames)

df_filtered = df[df["uploaded_filename"] == selected_file]

if df_filtered.empty:
    st.warning("⚠️ No data available for the selected file.")
    st.stop()

st.subheader("📄 Results Table")
st.dataframe(df_filtered, use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    fig_co2 = px.bar(
        df_filtered,
        x="tool_name",
        y="co2_emissions_kg",
        title="CO₂ Emissions (kg)",
        color="tool_name",
        text_auto=".6e",  # scientific notation for tiny values
        color_discrete_map={
            "eco2AI": "#4caf50",
            "CodeCarbon": "#388e3c",
            "CarbonTracker": "#81c784"
        },
        template="plotly_dark"
    )
    fig_co2.update_layout(
        plot_bgcolor="#182618",
        paper_bgcolor="#182618",
        font_color="#a8d5a3",
        title_font_size=20,
        title_font_color="#6bdc6b",
        margin=dict(t=50, b=30, l=40, r=40),
        yaxis=dict(
            type="log",  # logarithmic scale
            tickformat=".1e",  # scientific notation on ticks
            nticks= 6,
            showgrid=True, gridcolor='#2f4f2f', zerolinecolor='#4ca64c'
        ),
        xaxis=dict(showgrid=False)
    )
    fig_co2.update_traces(marker_line_color='black', marker_line_width=1.8)
    st.plotly_chart(fig_co2, use_container_width=True)

with col2:
    fig_power = px.bar(
        df_filtered,
        x="tool_name",
        y="power_kwh",
        title="Energy Consumption (kWh)",
        color="tool_name",
        text_auto=".6e",  # scientific notation for tiny values
        color_discrete_map={
            "eco2AI": "#2196f3",
            "CodeCarbon": "#1565c0",
            "CarbonTracker": "#64b5f6"
        },
        template="plotly_dark"
    )
    fig_power.update_layout(
        
        plot_bgcolor="#182f3e",
        paper_bgcolor="#182f3e",
        font_color="#a8d5a3",
        title_font_size=20,
        title_font_color="#5db7f5",
        margin=dict(t=50, b=30, l=40, r=40),
        yaxis=dict(
            type="log",  # logarithmic scale
            tickformat=".1e",
            nticks=6,
            showgrid=True, gridcolor='#2c4660', zerolinecolor='#2196f3'
        ),
        xaxis=dict(showgrid=False)
    )
    

    fig_power.update_traces(marker_line_color='black', marker_line_width=1.8)
    st.plotly_chart(fig_power, use_container_width=True)

with col3:
    fig_duration = px.bar(
        df_filtered,
        x="tool_name",
        y="duration_s",
        title="Execution Time (s)",
        color="tool_name",
        text_auto=".2f",
        color_discrete_map={
            "eco2AI": "#ff9800",
            "CodeCarbon": "#ef6c00",
            "CarbonTracker": "#ffb74d"
        },
        template="plotly_dark"
    )
    fig_duration.update_layout(
        plot_bgcolor="#3e2e18",
        paper_bgcolor="#3e2e18",
        font_color="#a8d5a3",
        title_font_size=20,
        title_font_color="#f4a42f",
        margin=dict(t=50, b=30, l=40, r=40),
        yaxis=dict(showgrid=True, gridcolor='#6f4b00', zerolinecolor='#ff9800'),
        xaxis=dict(showgrid=False)
    )
    fig_duration.update_traces(marker_line_color='black', marker_line_width=1.8)
    st.plotly_chart(fig_duration, use_container_width=True)

st.markdown("---")
st.markdown(
    f"✅ Comparison complete for **{selected_file}**. "
    "You can now visually analyze which tool has lower emissions, energy usage, and time.",
    unsafe_allow_html=True
)

import io
import plotly.express as px
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors


import io
import plotly.express as px
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors

def create_pdf(df_filtered, filename):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40
    )
   

    story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="MainTitle", alignment=TA_CENTER, fontSize=22,
                              spaceAfter=20, textColor=colors.HexColor("#1B5E20")))
    styles.add(ParagraphStyle(name="SectionHeading", alignment=TA_LEFT, fontSize=16,
                              spaceAfter=12, fontName="Helvetica-Bold" , textColor=colors.HexColor("#1B5E20")))
    styles.add(ParagraphStyle(name="CustomBullet", alignment=TA_LEFT, fontSize=11,
                              leading=16, spaceAfter=6))
    
    logo = Image("Project Logo.jpg", width=100, height=100)  # replace with your project logo path
    
    story.append(logo)
    styles.add(ParagraphStyle(
    name="Justify",
    parent=styles["Normal"],
    alignment=TA_LEFT,  # use TA_JUSTIFY if you want full justification
    fontSize=11,
    leading=16
    ))

    # === Title ===
    story.append(Paragraph("<b>GreenAI Comparometer Report</b>", styles["MainTitle"]))
    story.append(Spacer(1, 25))
    story.append(Paragraph(f"<b>File Analyzed:</b> {filename}", styles["Normal"]))
    story.append(Spacer(1, 25))

    # --- Executive Summary ---
    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    story.append(Spacer(1, 2))
    summary_text = f"""
    This report presents a comparative analysis of carbon emissions, power consumption, and
    execution duration for the selected file: <b>{filename}</b>. The analysis was conducted using
    three state-of-the-art tools: eco2AI, CodeCarbon, and CarbonTracker.

    Each tool provides different perspectives:
    - <b>eco2AI</b> gives lightweight and transparent emission tracking.
    - <b>CodeCarbon</b> offers detailed power and energy usage metrics.
    - <b>CarbonTracker</b> highlights efficiency trends over time and resources.

    The combined results give researchers and practitioners actionable insights into the
    environmental footprint of their machine learning experiments.
    """
    story.append(Paragraph(summary_text, styles["Justify"]))
    story.append(Spacer(1, 18))


    # === Results Table (auto-fit columns to page) ===
    story.append(Paragraph("Results Summary", styles["SectionHeading"]))
    story.append(Spacer(1, 20))
    cell_style = ParagraphStyle(name="CellStyle", fontSize=7, alignment=TA_CENTER)

    data = [list(df_filtered.columns)] + [
    [Paragraph(str(val), cell_style) for val in row]
    for row in df_filtered.values.tolist()
    ]
    page_width = doc.width
    col_count = len(data[0])
    col_widths = [200, 80, 80, 80, 80, 100]  # distribute equally

    table = Table(data, repeatRows=1, colWidths=col_widths, hAlign="CENTER")
    table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2E7D32")),  # header bg
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ("FONTSIZE", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,0), 5),
    ("TOPPADDING", (0,0), (-1,0), 5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), (colors.whitesmoke, colors.HexColor("#E8F5E9"))),
]))
    story.append(table)
    story.append(Spacer(1, 25))

    # === Charts ===
    story.append(PageBreak())
    story.append(Paragraph("Visualizations", styles["SectionHeading"]))
    story.append(Spacer(1, 25))

    def save_chart(fig, path):
        fig.write_image(path, format="png", width=500, height=400, scale=2)

    color_map = {"CodeCarbon": "#1565C0", "CarbonTracker": "#F57C00", "eco2AI": "#2E7D32"}

    def make_chart(y, title):
        fig = px.bar(df_filtered, x="tool_name", y=y, text_auto=".4f",
                     color="tool_name", color_discrete_map=color_map)
        fig.update_layout(title=title, font=dict(size=12))
        return fig

    save_chart(make_chart("co2_emissions_kg", "CO₂ Emissions (kg)"), "co2.png")
    save_chart(make_chart("power_kwh", "Energy Consumption (kWh)"), "energy.png")
    save_chart(make_chart("duration_s", "Execution Time (s)"), "duration.png")
    save_chart(px.pie(df_filtered, names="tool_name", values="co2_emissions_kg",
                      title="CO₂ Share by Tool", color="tool_name", color_discrete_map=color_map), "pie.png")

    # Add charts in 2x2 grid with borders
    for row_imgs in [["co2.png", "energy.png"], ["duration.png", "pie.png"]]:
        row = []
        for img in row_imgs:
            bordered_img = Table(
                [[Image(img, 250, 200)]],
                style=[
                    ("BOX", (0,0), (-1,-1), 1.5, colors.HexColor("#2E7D32")),
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ]
            )
            row.append(bordered_img)
        story.append(Table([row], hAlign="CENTER", colWidths=[260, 260]))
        story.append(Spacer(1, 15))

    # === Recommendations on New Page ===
    
    # --- Recommendations ---
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", styles["SectionHeading"]))
    story.append(Spacer(1, 20))

    recommendations_text = """
    Based on the comparative results from eco2AI, CodeCarbon, and CarbonTracker, we propose
    the following actionable steps to help researchers and practitioners reduce emissions
    and optimize energy efficiency in their workflows:
    """
    story.append(Paragraph(recommendations_text, styles["Justify"]))
    story.append(Spacer(1, 12))

    # Create bullet points in categories
    recommendations = [
        ("Code Optimization", [
            "Use efficient algorithms and avoid unnecessary model complexity.",
            "Experiment with reduced precision (e.g., FP16 instead of FP32) where possible.",
            "Apply early stopping to prevent wasteful long training runs.",
            "Leverage model pruning, quantization, and knowledge distillation."
        ]),
        ("Hardware Efficiency", [
            "Choose GPUs/TPUs optimized for efficiency rather than raw power when possible.",
            "Utilize cloud providers offering renewable-energy-backed infrastructure.",
            "Co-locate computations in data centers closer to renewable sources.",
            "Schedule runs during off-peak energy demand hours."
        ]),
        ("Experiment Management", [
            "Log and track carbon emissions for each run to build awareness over time.",
            "Batch and parallelize jobs smartly to reduce idle energy waste.",
            "Reuse intermediate results instead of retraining from scratch.",
            "Automate hyperparameter tuning efficiently to minimize redundant runs."
        ])
    ]

    from reportlab.platypus import ListFlowable, ListItem

    for category, items in recommendations:
        story.append(Paragraph(f"<b>{category}</b>", styles["Normal"]))
        bullet_list = ListFlowable(
            [ListItem(Paragraph(item, styles["Normal"])) for item in items],
            bulletType="bullet", start="•", leftIndent=20, bulletFontSize=10
        )
        story.append(bullet_list)
        story.append(Spacer(1, 20))


    # === Carbon Equivalence ===
    story.append(Paragraph("Carbon Impact Equivalence", styles["SectionHeading"]))
    story.append(Spacer(1, 20))
    total_co2 = df_filtered["co2_emissions_kg"].sum()
    equivalences = [
        f"≈ Driving a car for {total_co2*8.9:.1f} meters",
        f"≈ Charging a smartphone {total_co2*120000:.0f} times",
        f"≈ Powering a LED bulb for {total_co2*500:.1f} hours"
    ]
    for eq in equivalences:
        story.append(Paragraph(f"• {eq}", styles["CustomBullet"]))

    # --- Professional Conclusion ---
    story.append(Spacer(1, 24))
    story.append(Paragraph("Conclusion", styles["SectionHeading"]))
    story.append(Spacer(1, 20))
    conclusion_text = """
    The results of this analysis demonstrate that emissions and energy consumption vary depending
    on the chosen tool, the code tested, and the computational resources used. Despite these
    differences, all three tools consistently reinforce one key insight: optimizing AI workflows can
    substantially reduce carbon impact.

    To support sustainable AI practices, users are encouraged to:
    - Compare results across tools to gain a holistic perspective.
    - Apply optimization strategies recommended in this report.
    - Monitor emissions regularly as part of their research pipeline.

    By integrating these practices, the GreenAI Comparometer helps advance AI research that is
    both innovative and environmentally responsible.
    """
    story.append(Paragraph(conclusion_text, styles["Justify"]))


    doc.build(story)
    buffer.seek(0)
    return buffer




pdf_buffer = create_pdf(df_filtered, selected_file)

st.download_button(
    label="📥 Download Report (PDF)",
    data=pdf_buffer,
    file_name=f"{selected_file}_report.pdf",
    mime="application/pdf"
)
