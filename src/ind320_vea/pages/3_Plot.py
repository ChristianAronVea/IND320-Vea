import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.title("Plot")


@st.cache_data
def load_data():
    # Read the reservoir data from the local CSV file
    df = pd.read_csv("data/reservoirs.csv")

    # Rename columns to understandable English names
    df = df.rename(columns={
        "dato_Id": "date_Id",
        "omrType": "area_type",
        "omrnr": "area_number",
        "iso_aar": "iso_year",
        "iso_uke": "iso_week",
        "fyllingsgrad": "fill_rate",
        "kapasitet_TWh": "capacity_TWh",
        "fylling_TWh": "storage_TWh",
        "neste_Publiseringsdato": "next_publication_date",
        "fyllingsgrad_forrige_uke": "fill_rate_previous_week",
        "endring_fyllingsgrad": "fill_rate_change"
    })

    return df


df = load_data()

# Convert the date column to datetime
df["date_Id"] = pd.to_datetime(df["date_Id"])

# Keep the months as pandas Period values so they remain sortable and filterable.
month_values = df["date_Id"].dt.to_period("M")
months = sorted(month_values.dropna().unique())

# SLIDER
selected_month = st.select_slider(
    "Select month",
    options=months,
    value=months[0],
    format_func=str,
)

# SELECT BOX
# Only numeric measurements can be plotted against the date axis.
numeric_columns = [
    "fill_rate",
    "capacity_TWh",
    "storage_TWh",
    "fill_rate_previous_week",
    "fill_rate_change",
]
columns = ["All numeric columns"] + numeric_columns

# Let the user choose which column to plot
selected_column = st.selectbox(
    "Select data to plot",
    columns
)

st.write("Selected:", selected_column)



# Filter the data to the selected month
month_data = df[month_values == selected_month]

# Select the data to plot
if selected_column == "All numeric columns":
    plot_columns = numeric_columns
else:
    plot_columns = [selected_column]

plot_data = month_data[["date_Id"] + plot_columns].sort_values("date_Id")

# Create the plot
st.line_chart(plot_data, x="date_Id", y=plot_columns)