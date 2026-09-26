import streamlit as st
import pandas as pd

st.title("Reservoir Data")


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


# Load the data
df = load_data()

# Convert the date column to datetime
df["date_Id"] = pd.to_datetime(df["date_Id"])

# Find the first month in the dataset
first_month = df["date_Id"].min().to_period("M")

# Select all observations from the first month
first_month_df = df[
    df["date_Id"].dt.to_period("M") == first_month
]



st.write("First month:", first_month)

# Create one row for each column in the original dataset
chart_data = pd.DataFrame({
    "Variable": first_month_df.columns,
    "Values": [
        first_month_df[column].tolist()
        for column in first_month_df.columns
    ]
})

st.dataframe(
    chart_data,
    column_config={
        "Values": st.column_config.LineChartColumn(
            "First month"
        )
    },
    hide_index=True
)