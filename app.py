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

st.set_page_config(layout="wide")


def _project_id() -> str:
    """Use the Google Auth helper (via the metadata service) to get the Google Cloud Project"""
    try:
        _, project = google.auth.default()
    except google.auth.exceptions.DefaultCredentialsError as e:
        raise Exception("Could not automatically determine credentials") from e
    if not project:
        raise Exception("Could not determine project from credentials.")
    return project


def _region() -> str:
    """Use the local metadata service to get the region"""
    try:
        resp = httpx.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/region",
            headers={"Metadata-Flavor": "Google"},
        )
        return resp.text.split("/")[-1]
    except Exception:
        return "us-central1"


API_KEY = os.environ.get("GOOGLE_API_KEY")
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", _project_id())
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", _region())
MODELS = {
    "gemini-2.0-flash": "Gemini 2.0 Flash",
    "gemini-2.0-flash-lite": "Gemini 2.0 Flash-Lite",
    "gemini-2.5-pro-exp-03-25": "Gemini 2.5 Pro Experimental",
}


@st.cache_resource
def load_client() -> genai.Client:
    """Load Google Gen AI Client."""
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
        api_key=API_KEY,
    )


def get_model_name(name: str | None) -> str:
    """Get the formatted model name."""
    if not name:
        return "Gemini"
    return MODELS.get(name, "Gemini")


cloud_run_service = os.environ.get("K_SERVICE")
if cloud_run_service:
    st.link_button(
        "Open in Cloud Run",
        f"""https://console.cloud.google.com/run/detail/us-central1/{
            cloud_run_service}/source""",
    )

# --- Page Setup ---
st.header("Interactive Map Demo", divider="rainbow")
client = load_client()

# # Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([5, 2])

# --- Data Setup ---
rainfall = "data/rainfall_new_month_statewide_data_map_2012_03.tif"
temperature = "test.tif"

# Open the raster dataset
with rasterio.open("test.tif") as dataset:
    # Read the raster data into a NumPy array
    raster_data = dataset.read(1)  # Assuming single-band data
    # Normalize values for visualization
    raster_data_normalized = raster_data / raster_data.max()

    # Transform bounds to WGS84 (EPSG:4326)
    bounds = transform_bounds(dataset.crs, 'EPSG:4326', *dataset.bounds)

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

# --- Map Setup ---
with col1:
    hawaii_center = [21.483, -157.980]  # Latitude, Longitude

# Get saved state or fall back
    center = st.session_state.get("map_center", hawaii_center)
    zoom = st.session_state.get("map_zoom", 7)

    m = folium.Map(location=hawaii_center, zoom_start=zoom)


# Overlay the raster data
    folium.raster_layers.ImageOverlay(
        image=raster_data_normalized,
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        opacity=0.7

    ).add_to(m)
# Display the map and capture interaction
    result = st_folium(m, width=1280, height=720,
                       returned_objects=["last_center", "zoom"])

# Save the new state to prevent reset
    if result:
        st.session_state["map_center"] = result.get(
            "last_center", hawaii_center)
        st.session_state["map_zoom"] = result.get("zoom", zoom)
