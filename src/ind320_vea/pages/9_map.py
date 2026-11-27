import streamlit as st


import json
from pathlib import Path

import geopandas as gpd
import pydeck as pdk
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AREA_DATASETS = {
    "Price areas (Budområder)": {
        "path": PROJECT_ROOT / "Notebooks" / "data" / "Budområder" / "Budområder.geojson",
        "tooltip": "<b>{budomr}</b>",
    },
    "NVE regions": {
        "path": PROJECT_ROOT / "Notebooks" / "data" / "NVE_Region" / "NVE_Region.geojson",
        "tooltip": "<b>{REGIONNAVN}</b>",
    },
}


@st.cache_data
def load_area_geojson(path: str):
    areas = gpd.read_file(path)
    if areas.crs is None:
        raise ValueError(f"Area file has no coordinate reference system: {path}")

    areas = areas.to_crs(epsg=4326)
    return json.loads(areas.to_json()), areas.total_bounds.tolist(), len(areas)


st.title("Map and selectors")
st.caption("Explore the outlines of the available Norwegian area datasets.")

selected_dataset = st.radio("Area dataset", list(AREA_DATASETS), horizontal=True)
dataset = AREA_DATASETS[selected_dataset]
geojson, bounds, feature_count = load_area_geojson(str(dataset["path"]))
min_lon, min_lat, max_lon, max_lat = bounds

layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson,
    stroked=True,
    filled=False,
    pickable=False,
    get_line_color=[27, 115, 144, 230],
    get_line_width=2,
    line_width_min_pixels=2,
)
view_state = pdk.ViewState(
    longitude=(min_lon + max_lon) / 2,
    latitude=(min_lat + max_lat) / 2,
    zoom=3.3,
)
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"html": dataset["tooltip"]},
)

st.pydeck_chart(deck, use_container_width=True)
st.caption(f"{feature_count} areas shown. Click/selection will be added in a later step.")
