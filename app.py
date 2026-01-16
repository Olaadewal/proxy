import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Quarry Truck Production Dashboard", layout="wide")
st.title("Quarry Truck Production Dashboard")

@st.cache_data
def load_and_normalize():
    # Read with two header rows
    raw = pd.read_excel("Production.xlsx", header=[0, 1])
    raw.columns = [
        f"{a}_{b}".strip("_")
        for a, b in raw.columns
    ]

    # Identify truck columns by position
    # Date is always first
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

st.sidebar.header("Filters")

selected_date = st.sidebar.date_input(
    "Select Date",
    df["Date"].min().date()
)

selected_trucks = st.sidebar.multiselect(
    "Select Trucks",
    sorted(df["Truck"].unique()),
    default=sorted(df["Truck"].unique())
)

filtered_df = df[
    (df["Date"] == pd.to_datetime(selected_date)) &
    (df["Truck"].isin(selected_trucks))
]

trend_df = df[df["Truck"].isin(selected_trucks)]

st.subheader("Key Metrics")

c1, c2, c3 = st.columns(3)

c1.metric("Total Tons", f"{filtered_df['Total_Tons'].sum():,.0f}")
c2.metric(
    "Average Truck Load",
    f"{filtered_df['Total_Tons'].mean():.1f}" if not filtered_df.empty else "0"
)
c3.metric("Max Capacity", MAX_CAPACITY)

st.subheader("Daily Truck Load")

if not filtered_df.empty:
    fig_bar = px.bar(
        filtered_df,
        x="Truck",
        y="Total_Tons",
        text="Total_Tons"
    )
    fig_bar.add_hline(y=MAX_CAPACITY, line_dash="dash", line_color="red")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.warning("No data for selected filters.")

st.subheader("Truck Load Trend Over Time")

fig_trend = px.line(
    trend_df,
    x="Date",
    y="Total_Tons",
    color="Truck",
    markers=True
)
fig_trend.add_hline(y=MAX_CAPACITY, line_dash="dash", line_color="red")
st.plotly_chart(fig_trend, use_container_width=True)

st.subheader("Normalized Truck Data")
st.dataframe(df)
