#!/bin/bash
# Script name: HiAaronIly.sh
# Author: Lars, Jack, Olamide
# Date: March 7, 2024
# Description: This script installs the dependencies and runs the code. 

# ubuntu 
# sudo apt update
# sudo apt install tmux
brew install tmux


# Start a new tmux session named "fila_forge"
tmux new-session -d -s fila_forge

# split vertically 
tmux split-window -v


tmux send-keys -t fila_forge:0.0 '
  echo "FLASK_ENV=development" > .env &&
  echo "FLASK_APP=app.py" >> .env &&
  echo "FLASK_RUN_PORT=8000" >> .env &&
  echo "SQLALCHEMY_DATABASE_URI=hvamc.db" >> .env &&
  echo "BASE_URL=http://localhost:8000" >> .env
' Enter

# install the dependencies 
tmux send-keys -t fila_forge:0.0 '
cd server &&
pip freeze > requirements. txt && 
pip install -r requirements.txt && 
flask db init &&
flask db migrate &&
flask db upgrade &&
flask run 
' Enter 

# set environment variables
# FLASK_ENV=development
# FLASK_APP=app.py
# FLASK_RUN_PORT=8000
# SQLALCHEMY_DATABASE_URI=hvamc.db
# BASE_URL=http://localhost:8000

# Write environment variables to .env file
# echo "FLASK_ENV=$FLASK_ENV" > .env
# echo "FLASK_APP=$FLASK_APP" >> .env
# echo "FLASK_RUN_PORT=$FLASK_RUN_PORT" >> .env
# echo "SQLALCHEMY_DATABASE_URI=$SQLALCHEMY_DATABASE_URI" >> .env
# echo "BASE_URL=$BASE_URL" >> .env

# Run 
# flask run 

tmux send-keys -t fila_forge:0.1 '
  echo "VITE_API_ROOT=http://localhost:8000" > .env 
' Enter

# install dependencies in client 
tmux send-keys -t fila_forge:0.1 '
  cd client &&
  npm i &&
  npm i vite@latest &&
  npm run dev
' Enter

# cd ..
# cd client 
# npm i 
# npm i vite@latest 
# npm run dev 