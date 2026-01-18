import streamlit as st
import pandas as pd
import plotly.express as px

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Quarry Truck Production Dashboard", layout="wide")
st.title("Quarry Truck Production Dashboard")

# -------------------------------------------------
# TRUCK COLOR MAP
# -------------------------------------------------
TRUCK_COLORS = {
    "Lemon": "#FFD700",   # Lemon / Gold
    "Blue": "#1F77B4",    # Blue
    "Yellow": "#FFB000",  # Distinct Yellow/Orange
    "Black": "#000000",   # Black
}

# -------------------------------------------------
# LOAD + NORMALIZE DATA
# -------------------------------------------------
@st.cache_data
def load_and_normalize():
    raw = pd.read_excel("Production.xlsx", header=[0, 1])
    raw.columns = [f"{a}_{b}".strip("_") for a, b in raw.columns]

    date_col = raw.columns[0]
    truck_blocks = {
        "Lemon": raw.columns[1:3],
        "Blue": raw.columns[3:5],
        "Yellow": raw.columns[5:7],
        "Black": raw.columns[7:9],
    }

    records = []
    for truck, cols in truck_blocks.items():
        temp = raw[[date_col, cols[0], cols[1]]].copy()
        temp.columns = ["Date", "Crusher", "ROM_PAD"]
        temp["Truck"] = truck
        records.append(temp)

    df = pd.concat(records, ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Crusher"] = pd.to_numeric(df["Crusher"], errors="coerce").fillna(0)
    df["ROM_PAD"] = pd.to_numeric(df["ROM_PAD"], errors="coerce").fillna(0)
    df["Total_Tons"] = df["Crusher"] + df["ROM_PAD"]
    return df

df = load_and_normalize()

MAX_CAPACITY = 20

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("Filters")

time_view = st.sidebar.selectbox("Time View", ["Daily", "Weekly", "Monthly"])

selected_trucks = st.sidebar.multiselect(
    "Select Trucks",
    sorted(df["Truck"].unique()),
    default=sorted(df["Truck"].unique())
)

df = df[df["Truck"].isin(selected_trucks)]

# -------------------------------------------------
# HANDLE NaT DATES
# -------------------------------------------------
df = df.dropna(subset=["Date"]).copy()

# -------------------------------------------------
# TIME AGGREGATION
# -------------------------------------------------
if time_view == "Daily":
    selected_date = st.sidebar.date_input("Select Date", df["Date"].min().date())
    df = df[df["Date"] == pd.to_datetime(selected_date)]
    df["Period"] = df["Date"]  # Period is just the day for daily
elif time_view == "Weekly":
    df["Period"] = df["Date"].dt.to_period("W").dt.start_time
else:  # Monthly
    df["Period"] = df["Date"].dt.to_period("M").dt.start_time

agg_df = df.groupby(["Period", "Truck"], as_index=False).agg({"Total_Tons": "sum"})

# -------------------------------------------------
# KPIs
# -------------------------------------------------
st.subheader("Key Metrics")
c1, c2, c3 = st.columns(3)

c1.metric("Total Tons", f"{agg_df['Total_Tons'].sum():,.0f}")
c2.metric("Average Truck Load", f"{agg_df['Total_Tons'].mean():.1f}" if not agg_df.empty else "0")
# Max capacity only meaningful for daily
c3.metric("Max Capacity", f"{MAX_CAPACITY}" if time_view == "Daily" else "—")

# -------------------------------------------------
# BAR CHART
# -------------------------------------------------
st.subheader(f"{time_view} Truck Load")
fig_bar = px.bar(
    agg_df,
    x="Truck",
    y="Total_Tons",
    color="Truck",
    text="Total_Tons",
    title=f"{time_view} Truck Load",
    color_discrete_map=TRUCK_COLORS
)
if time_view == "Daily":
    fig_bar.add_hline(y=MAX_CAPACITY, line_dash="dash", line_color="red")
st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------
# TREND CHART
# -------------------------------------------------
st.subheader("Truck Load Trend Over Time")
fig_trend = px.line(
    agg_df,
    x="Period",
    y="Total_Tons",
    color="Truck",
    markers=True,
    title="Production Trend",
    color_discrete_map=TRUCK_COLORS
)
if time_view == "Daily":
    fig_trend.add_hline(y=MAX_CAPACITY, line_dash="dash", line_color="red")
st.plotly_chart(fig_trend, use_container_width=True)

# -------------------------------------------------
# PDF EXPORT
# -------------------------------------------------
def generate_pdf(bar_fig, trend_fig, time_view):
    tmpdir = tempfile.mkdtemp()
    bar_path = os.path.join(tmpdir, "bar.png")
    trend_path = os.path.join(tmpdir, "trend.png")

    bar_fig.write_image(bar_path, width=900, height=500)
    trend_fig.write_image(trend_path, width=900, height=500)

    pdf_path = os.path.join(tmpdir, "quarry_report.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Quarry Truck Production Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"View: {time_view}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Truck Load Summary", styles["Heading2"]))
    elements.append(Image(bar_path, width=450, height=260))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Production Trend", styles["Heading2"]))
    elements.append(Image(trend_path, width=450, height=260))

    doc.build(elements)
    return pdf_path

st.subheader("Export Report")
if st.button("Generate PDF Report"):
    pdf_file = generate_pdf(fig_bar, fig_trend, time_view)
    with open(pdf_file, "rb") as f:
        st.download_button(
            "Download PDF",
            data=f,
            file_name="quarry_truck_report.pdf",
            mime="application/pdf"
        )

# -------------------------------------------------
# DATA TABLE
# -------------------------------------------------
st.subheader("Normalized Truck Data")
st.dataframe(df)
