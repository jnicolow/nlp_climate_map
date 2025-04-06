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

st.set_page_config(layout="wide")


cloud_run_service = os.environ.get("K_SERVICE")
if cloud_run_service:
    st.link_button(
        "Open in Cloud Run",
        f"""https://console.cloud.google.com/run/detail/us-central1/{
            cloud_run_service}/source""",
    )

# --- Page Setup ---
st.header("Interactive Map Demo", divider="rainbow")
client = gutils.gcloud_auth()  # sets up gcloud client to get llm response


# # Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([5, 2])

# --- Data Setup ---
rainfall = "data/rainfall_new_month_statewide_data_map_2012_03.tif"
temperature = "test.tif"
raster_data_normalized = None

# Open the raster dataset
# with rasterio.open("test.tif") as dataset:
#    # Read the raster data into a NumPy array
#    raster_data = dataset.read(1)  # Assuming single-band data
#    # Normalize values for visualization
#    raster_data_normalized = raster_data / raster_data.max()
#
#    # Transform bounds to WGS84 (EPSG:4326)
#    bounds = transform_bounds(dataset.crs, 'EPSG:4326', *dataset.bounds)


# --- Map Setup ---
with col1:
    hawaii_center = [21.483, -157.980]  # Latitude, Longitude

# Get saved state or fall back
    center = st.session_state.get("map_center", hawaii_center)
    zoom = st.session_state.get("map_zoom", 7)

    m = folium.Map(location=hawaii_center, zoom_start=zoom)


# Display the map and capture interaction
    result = st_folium(m, width=1280, height=720,
                       returned_objects=["last_center", "zoom"])

# Save the new state to prevent reset
    if result:
        st.session_state["map_center"] = result.get(
            "last_center", hawaii_center)
        st.session_state["map_zoom"] = result.get("zoom", zoom)


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

    assert (prompt is not None)
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
    if raster_data_normalized is not None:
        folium.raster_layers.ImageOverlay(
            image=raster_data_normalized,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=0.7

        ).add_to(m)
# Display the map and capture interaction
# --- Map Setup ---
with col1:
    hawaii_center = [21.483, -157.980]  # Latitude, Longitude

# Get saved state or fall back
    center = st.session_state.get("map_center", hawaii_center)
    zoom = st.session_state.get("map_zoom", 7)


# Display the map and capture interaction
    result = st_folium(m, width=1280, height=720, returned_objects=["last_center", "zoom"])

    folium.raster_layers.ImageOverlay(
        image=raster_data_normalized,
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        opacity=0.7

    ).add_to(m)

# Save the new state to prevent reset
    if result:
        st.session_state["map_center"] = result.get(
            "last_center", hawaii_center)
        st.session_state["map_zoom"] = result.get("zoom", zoom)
