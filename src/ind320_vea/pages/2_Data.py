import pandas as pd
import streamlit as st

from ind320_vea.help_functions import load_data

st.title("Reservoir Data")

df = load_data()

# Convert the date column to datetime
df["date_Id"] = pd.to_datetime(df["date_Id"])

# Sort the data chronologically before creating the table
df = df.sort_values("date_Id").reset_index(drop=True)

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