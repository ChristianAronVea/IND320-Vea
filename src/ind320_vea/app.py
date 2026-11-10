# app.py
import streamlit as st
from pathlib import Path

pages_folder = Path(__file__).parent / "pages"

pages = [
    st.Page(pages_folder / "1_Home.py", title="Home"),
    st.Page(pages_folder / "2_Data.py", title="Data"),
    st.Page(pages_folder / "3_Plot.py", title="Plot"),
    st.Page(pages_folder / "4_ENTSOE.py", title="ENTSOE"),
    st.Page(pages_folder / "5_About.py", title="About"),
]

page = st.navigation(pages)
page.run()