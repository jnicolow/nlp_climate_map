import os

from google import genai
import google.auth
from google.genai.types import GenerateContentConfig, Part
import httpx
import streamlit as st
from google.genai import types
import re
import json

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


def gcloud_auth():
        
    # API_KEY = os.environ.get("GOOGLE_API_KEY")
    PROJECT_ID = 'alohadata-team5'#os.environ.get("GOOGLE_CLOUD_PROJECT")
    LOCATION = 'us-central1'#os.environ.get("GOOGLE_CLOUD_REGION", _region())
    # MODELS = {
    #     "gemini-2.0-flash": "Gemini 2.0 Flash",
    #     "gemini-2.0-flash-lite": "Gemini 2.0 Flash-Lite",
    #     "gemini-2.5-pro-exp-03-25": "Gemini 2.5 Pro Experimental",
    # }

    def load_client() -> genai.Client:
        """Load Google Gen AI Client."""
        return genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
            # api_key=API_KEY,
        )

    client = load_client()
    return client


def answer_prompty(prompt, client=None):
   if client is None: client = gcloud_auth()
   
   si_text = """
   ## Task Definition
   The user requests climate data (temperature or rainfall) for the Hawaiian Islands. The model returns two responses.

   ## Input Format
   - Inputs in natural language text.
   - Queries for temperature or rainfall for the main hawaiian islands: Kauai, Oahu, Molokai, Lanai, Maui and Big Island.
   - Queries must specify a year or month.
   - Only one "aggregates" ("min", "mean", or "max") and only one "product_type" ('rainfall' or 'temperature'). Otherwise, ask for clarification.
   - Support for multiple months and years.
   - Full year average allowed: use 'month':None.
   - If asked for Hawaii, 'island':'all'.
   - Only data before 2025.
   - No support for overall min or max accross the whole dataset.
   - If input doesn't follow rules, respond: "Sorry, I cannot help you with that. If you want, you can ask me about yearly or monthly temperature or rain information of the main Hawaiian Islands".

   ## Output Format
   - Two outputs.
   1. JSON output (no new lines): "{'island':'Kauai', 'Oahu', 'Molokai', 'Lanai', 'Maui' or 'Big Island', "product_type":'rainfall' or 'temperature', 'year':YYYY, 'month':MM, 'aggregation':'min','mean' or 'max'}"
      - Use list for multiple years or months.
      - For multiple months of the same year, repeat the year per month.
   2. Text output:
      - Concise and accurate natural-language summary (maximum 100 words).
      - Describe what the user will see.

   ## Example Scenarios
   1. **User:** "How much did it rain in Hawaii in January of 2020?"
      - **Model Response 1:** "{'island':'all','product_type':'rainfall', 'year':2020, 'month':01, 'aggregation':'mean'}"
      - **Model Response 2:** "I will show you a map of the average amount of rain in Hawaii in January of 2020.

   2. **User:** "How much did it rain in Kauai in January and July of 2020?"
      - **Model Response 1:** "{'island':'Kauai','product_type':'rainfall', 'year':[2020, 2020], 'month':[01,07], 'aggregation':'mean'}"
      - **Model Response 2:** "I will show you a map of the average amount of rain in Hawaii in January of 2020.

   3. **User:** "How hot did it get on Lanai in August of 1980?"
      - **Model Response 1:** "{'island':'Lanai','product_type':'temperature', 'year':[1980], 'month':[08], 'aggregation':'max'}"
      - **Model Response 2:** "I will show you the maximum temperature on Lanai in August of 1980 with a map.

   """

   config = GenerateContentConfig(
      temperature = 0,
      top_p = 0.1,
      max_output_tokens = 200,
      response_modalities = ["TEXT"],
      system_instruction=[types.Part.from_text(text=si_text)],
   )

   response = client.models.generate_content(
      model="gemini-2.0-flash-lite",
      contents=prompt,
      config=config,
   )

   return response.text

def clean_prompty(text):

    match = re.search(r"\{.*?\}", text, re.DOTALL)  # this gets the portion within curly brackets
    if match:
        dict_string = match.group(0) 
        # print(dict_string)
        # dict_string = dict_string.replace('"', '').strip()  # Remove double quotes and strip whitespace

        dict_string = dict_string.replace("'", '"')  # replace single quotes with double quotes
        dict_string = dict_string.replace('None', '"None"')
        # dict_string = re.sub(r'(\b\w+\b)', r'"\1"', dict_string)  # wrap words with double quotes
        # print(dict_string)
        json_data = json.loads(dict_string)
        if json_data['month'] == "None": json_data['month'] = None
        if json_data['month'] == 'null': json_data['month'] = None
        if isinstance(json_data['year'],list): json_data['year'] = json_data['year'][0]
        return json_data
        # print(json_data)
    
    print("No dictionary found in the input string.")
    return {'product_type':'rainfall', 'year':'2020'}
