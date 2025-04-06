# pylint: disable=broad-exception-caught,broad-exception-raised,invalid-name
"""
This module demonstrates the usage of the Gemini API in Vertex AI within a Streamlit application.
"""

import os

from google import genai
import google.auth
from google.genai.types import GenerateContentConfig, Part
import httpx
import streamlit as st
import rasterio
import folium
from streamlit_folium import st_folium
from rasterio.warp import transform_bounds

from gutils import gutils
from hcdp import hcdp

CENTER_START = [20.65, -157.3319]
ZOOM_START = 7.5

st.set_page_config(layout="wide")


# --- Page Setup ---
st.header("Interactive Map Demo", divider="rainbow")
client = gutils.gcloud_auth()  # sets up gcloud client to get llm response


# # Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "feature_group" not in st.session_state:
    st.session_state["feature_group"] = folium.FeatureGroup(name="Layer")

if "center" not in st.session_state:
    st.session_state["center"] = [20.65, -157.3319]

if "zoom" not in st.session_state:
    st.session_state["zoom"] = 7.5

col1, col2 = st.columns([5, 2])


# --- Map Setup ---

# Create the map

m = folium.Map(location=CENTER_START, zoom_start=ZOOM_START)

# --- Chat Bot Setup ---

with col2:

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        response_txt = gutils.answer_prompty(prompt)
        json_data = gutils.clean_prompty(response_txt)
        if isinstance(json_data['month'], list):
            json_data['month'] = json_data['month'][0]
        file_api = hcdp.FileDownloadAPI(
            product_type=json_data['product_type'], year=json_data['year'], month=json_data['month'], aggregation=json_data['aggregation'])
        dataset = file_api.get_data()

        # prep rasterio for plot
        raster_data_normalized = dataset.read(1) / dataset.read(1).max()

        # Transform bounds to WGS84 (EPSG:4326)
        bounds = transform_bounds(dataset.crs, 'EPSG:4326', *dataset.bounds)

        # Overlay the raster data
        layer = folium.raster_layers.ImageOverlay(
            image=raster_data_normalized,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=0.7

        )
        st.session_state["feature_group"].add_child(layer)

with col1:


    # Show the map and capture the interaction state
    result = st_folium(m, center=st.session_state["center"], zoom=st.session_state["zoom"], key="new", feature_group_to_add=st.session_state["feature_group"], width=1280, height=720, returned_objects=[])

