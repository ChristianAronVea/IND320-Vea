import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ind320_vea.help_functions import load_data


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AREA_DATASETS = {
    "Price areas": {
        "path": PROJECT_ROOT / "Notebooks" / "data" / "Budområder" / "Budområder.geojson",
    },
    "NVE regions": {
        "path": PROJECT_ROOT / "Notebooks" / "data" / "NVE_Region" / "NVE_Region.geojson",
    },
}
VASS_AREA_BY_REGION = {
    # Map each NVE region to its Magasinstatistikk water area.
    "RV": 2,
    "RS": 1,
    "RØ": 1,
    "RM": 3,
    "RN": 3,
}
MEASURES = {
    "Fill rate": ("fill_rate", "percent"),
    "Stored water (TWh)": ("storage_TWh", "TWh"),
    "Capacity (TWh)": ("capacity_TWh", "TWh"),
}


@st.cache_data
def load_area_geojson(path: str):
    # Convert the polygons to latitude and longitude for the map.
    areas = gpd.read_file(path, encoding="utf-8")
    if areas.crs is None:
        raise ValueError(f"Area file has no coordinate reference system: {path}")

    areas = areas.to_crs(epsg=4326)
    return json.loads(areas.to_json()), areas.total_bounds.tolist(), len(areas)


def select_map_area():
    # Update the sidebar area before app.py creates its selectbox.
    points = st.session_state["map_area_chart"]["selection"]["points"]
    if points:
        area_type, area_number = points[-1]["customdata"][:2]
        st.session_state["selected_area"] = (area_type, int(area_number))


st.title("Map and selectors")
st.caption("Explore area boundaries and reservoir data for the selected date.")

selected_dataset = st.radio("Area dataset", list(AREA_DATASETS), horizontal=True)
selected_measure = st.selectbox("Reservoir measure", list(MEASURES))
measure_column, measure_unit = MEASURES[selected_measure]
reservoir_data = load_data()
latest_date = reservoir_data["date_Id"].max().date()
selected_date = st.date_input(
    "Data date",
    value=latest_date,
    min_value=reservoir_data["date_Id"].min().date(),
    max_value=latest_date,
    key="map_selected_date",
)

dataset = AREA_DATASETS[selected_dataset]
geojson, bounds, feature_count = load_area_geojson(str(dataset["path"]))
min_lon, min_lat, max_lon, max_lat = bounds

# Use the latest measurement available on or before the selected date.
observations = reservoir_data.loc[
    reservoir_data["date_Id"] <= pd.Timestamp(selected_date)
].sort_values("date_Id")
if selected_dataset == "Price areas":
    observations = observations.loc[observations["area_type"] == "EL"]
else:
    observations = observations.loc[observations["area_type"] == "VASS"]

latest_by_area = observations.drop_duplicates("area_number", keep="last")
values_by_area = latest_by_area.set_index("area_number")[measure_column].to_dict()

# Match each map polygon with its reservoir area number.
map_values = []
for feature in geojson["features"]:
    properties = feature["properties"]
    if selected_dataset == "Price areas":
        area_number = int(properties["budomr"].split()[-1])
        map_id = properties["budomr"]
        area_name = properties["budomr"]
    else:
        area_number = VASS_AREA_BY_REGION.get(properties.get("REGION"))
        map_id = properties["REGION"]
        area_name = properties["REGIONNAVN"]

    value = values_by_area.get(area_number) if area_number is not None else None
    if pd.notna(value):
        map_values.append(
            {
                "map_id": map_id,
                "area_name": area_name,
                "area_type": "EL" if selected_dataset == "Price areas" else "VASS",
                "area_number": area_number,
                "value": float(value),
                "display_value": (
                    f"{value:.1%}" if measure_unit == "percent" else f"{value:.2f} TWh"
                ),
            }
        )
    properties["map_id"] = map_id

if map_values:
    map_data = pd.DataFrame(map_values)
    low, high = map_data["value"].min(), map_data["value"].max()
    if low == high:
        high = low + 1

    fig = px.choropleth_map(
        map_data,
        geojson=geojson,
        locations="map_id",
        featureidkey="properties.map_id",
        color="value",
        custom_data=["area_type", "area_number"],
        hover_name="area_name",
        hover_data={"value": False, "display_value": True},
        color_continuous_scale=[
            (0, "rgba(27, 115, 144, 0.43)"),
            (1, "rgba(207, 119, 31, 0.43)"),
        ],
        range_color=(low, high),
        map_style="open-street-map",
        center={"lat": (min_lat + max_lat) / 2, "lon": (min_lon + max_lon) / 2},
        zoom=3.3,
    )
    fig.update_traces(marker_line_width=2, marker_line_color="#1b7390")
    selected_area = st.session_state.get("selected_area")
    selected_map_ids = [
        area["map_id"]
        for area in map_values
        if (area["area_type"], area["area_number"]) == selected_area
    ]
    if selected_map_ids:
        selected_map_data = map_data.loc[map_data["map_id"].isin(selected_map_ids)]
        # Draw a transparent layer to outline the selected area.
        fig.add_trace(
            go.Choroplethmap(
                geojson=geojson,
                locations=selected_map_ids,
                featureidkey="properties.map_id",
                z=[1] * len(selected_map_ids),
                customdata=selected_map_data[
                    ["area_type", "area_number"]
                ].to_numpy().tolist(),
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker={"line": {"color": "#e63946", "width": 5}},
                hoverinfo="skip",
            )
        )
    fig.update_layout(
        clickmode="event+select",
        coloraxis_colorbar={
            "title": selected_measure,
            "tickformat": ".0%" if measure_unit == "percent" else ".2f",
        },
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=650,
    )
    st.plotly_chart(
        fig,
        key="map_area_chart",
        on_select=select_map_area,
        selection_mode="points",
        width="stretch",
    )
else:
    st.warning("No reservoir measurements are available for this date.")

effective_date = observations["date_Id"].max().date() if not observations.empty else None

st.caption(
    f"Latest available observation on or before the selected date: {effective_date}."
)
