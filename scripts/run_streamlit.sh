#!/bin/bash

$HOME/clean_port.sh 8080

cd $HOME/generative-ai/gemini/sample-apps/gemini-streamlit-cloudrun
source gemini-streamlit/bin/activate
source $HOME/.env

LOGFILE=$HOME/streamlit-logs/$(date +"%Y%m%d%H%M").log

nohup streamlit run app.py \
  --browser.serverAddress=localhost \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false \
  --server.port 8080 > $LOGFILE 2>&1 &

JS2_IP=`dig +short myip.opendns.com @resolver1.opendns.com`

echo "Your application should be running at ${JS2_IP}:8080. Please go to this address in a web browser to view the application. Logs can be found at $LOGFILE. To stop the application run $HOME/clean_port.sh 8080"
