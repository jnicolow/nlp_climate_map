#!/bin/bash

gcloud auth revoke --all
gcloud auth application-default revoke
rm $HOME/.config/gcloud/application_default_credentials.json
rm $HOME/Google-VertexAI-FastAPI/app/service_account.json
rm $HOME/.env
rm $HOME/service_account.json
rm $HOME/streamlit-logs/*
rm $HOME/fast-api-logs/*
$HOME/clean_port.sh 8080
$HOME/clean_port.sh 8081
