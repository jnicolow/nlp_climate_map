#!/bin/bash

if [ -n "$1" ]; then
  PIDS=`lsof -t -i :$1`
  if [ -n "$PIDS" ]; then
    echo "Killing processes ${PIDS//$'\n'/', '}"
    kill -9 $PIDS
  else
    echo "No processes are using port $1"
  fi
else
  echo "No port provided"
fi
