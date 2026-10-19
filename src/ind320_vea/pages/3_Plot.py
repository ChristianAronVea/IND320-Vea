import streamlit as st
import pandas as pd

from ind320_vea.help_functions import load_data

st.title("Plot")

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
    value=(months[0], months[1]),
    format_func=str,
)

# Let the user choose which reservoir area to plot
area_options = sorted(
    df[["area_type", "area_number"]]
    .drop_duplicates()
    .itertuples(index=False, name=None)
)
selected_area = st.selectbox(
    "Select reservoir area",
    area_options,
    format_func=lambda area: f"{area[0]} - area {area[1]}",
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



# Filter the data to the selected month range
month_data = df[
    (month_values >= selected_month[0])
    & (month_values <= selected_month[1])
    & (df["area_type"] == selected_area[0])
    & (df["area_number"] == selected_area[1])
]

# Select the data to plot
if selected_column == "All numeric columns":
    plot_columns = numeric_columns
else:
    plot_columns = [selected_column]

plot_data = month_data[["date_Id"] + plot_columns].sort_values("date_Id")

# Create the plot
st.line_chart(plot_data, x="date_Id", y=plot_columns)