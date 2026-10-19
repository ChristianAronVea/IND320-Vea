import pandas as pd
import requests
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient


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



# Connect wit MongoDB - local and by cloud
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / "atlas-credentials.env")     # local


@st.cache_resource
def get_mongo_client() -> MongoClient:
    uri = os.getenv("MONGODB_URI")

    if not uri and "MONGODB_URI" in st.secrets:
        uri = st.secrets["MONGODB_URI"]                 # cloud

    if not uri:
        raise RuntimeError("MONGODB_URI missing")

    return MongoClient(uri)


@st.cache_data
def load_crossborder_data() -> pd.DataFrame:
    client = get_mongo_client()
    collection = client["entsoe"]["crossborder_flows"]

    documents = list(collection.find({}, {"_id": 0}))
    if not documents:
        raise RuntimeError(
            "MongoDB collection entsoe.crossborder_flows contains no data"
        )

    df = pd.DataFrame(documents)
    df["ts"] = pd.to_datetime(df["ts"])
    return df.sort_values("ts").reset_index(drop=True)