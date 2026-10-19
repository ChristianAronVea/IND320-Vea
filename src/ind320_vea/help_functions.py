import pandas as pd
import requests
import streamlit as st


API_NVE = ("https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData")


@st.cache_data
def load_data(start_date=None, end_date=None):
    response = requests.get(API_NVE, timeout=30)
    response.raise_for_status()

    df = pd.DataFrame(response.json())

    # Convert the names from norwegian to english
    df = df.rename(
        columns={
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
            "endring_fyllingsgrad": "fill_rate_change",
        }
    )

    df["date_Id"] = pd.to_datetime(df["date_Id"])

    if start_date is not None:
        df = df[df["date_Id"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        df = df[df["date_Id"] <= pd.Timestamp(end_date)]

    return df.copy()
