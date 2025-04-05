#!/bin/bash

$HOME/clean_port.sh 8081

cd $HOME/Google-VertexAI-FastAPI/
source vertex-fastapi/bin/activate
cd app
source $HOME/.env

LOGFILE=$HOME/fast-api-logs/$(date +"%Y%m%d%H%M").log

nohup uvicorn main:app --host 0.0.0.0 --reload --port 8081 > $LOGFILE 2>&1 &

JS2_IP=`dig +short myip.opendns.com @resolver1.opendns.com`

echo "Your application should be running at ${JS2_IP}:8081. Please view ${JS2_IP}:8081/docs in a web browser for documentation on the available endpoints. Logs can be found at $LOGFILE. To stop the application run $HOME/clean_port.sh 8081"
