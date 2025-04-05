#!/bin/bash

cd $HOME/generative-ai/gemini/sample-apps/gemini-streamlit-cloudrun
source gemini-streamlit/bin/activate
read -p "Enter your Google Cloud project ID: " PROJECT
echo "export GOOGLE_CLOUD_PROJECT='$PROJECT';export GOOGLE_CLOUD_REGION='us-central1'" > $HOME/.env
source $HOME/.env

echo -e "\nAuthenticating to the Google Cloud CLI"
gcloud auth login

echo -e "\nCreating application default credentials (ADC)"
gcloud auth application-default login

gcloud services enable cloudbuild.googleapis.com cloudfunctions.googleapis.com run.googleapis.com logging.googleapis.com storage-component.googleapis.com aiplatform.googleapis.com

SERVICE_ACCOUNT_ID="general-service"
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_ID@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com

if [ -z `gcloud iam service-accounts list --filter="email:$SERVICE_ACCOUNT_EMAIL" --project="$GOOGLE_CLOUD_PROJECT" --format='value(email)'` ]; then
    echo -e "\nCreating service account $SERVICE_ACCOUNT_EMAIL"

    gcloud iam service-accounts create $SERVICE_ACCOUNT_ID \
        --display-name="Basic service account for general usage" \
        --project=$GOOGLE_CLOUD_PROJECT

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/editor"
fi

cd $HOME
gcloud iam service-accounts keys create service_account.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL \
    --project=$GOOGLE_CLOUD_PROJECT

cp service_account.json $HOME/Google-VertexAI-FastAPI/app

echo -e "\nService account credentials exported to $HOME/service_account.json"

echo "export SERVICE_ACCOUNT_EMAIL='$SERVICE_ACCOUNT_EMAIL'" >> $HOME/.env
