#!/bin/bash
# Script name: HiAaronIly.sh
# Author: Lars, Jack, Olamide
# Date: March 7, 2024
# Description: This script installs the dependencies and runs the code. 

# install tmux  
sudo apt update
sudo apt install tmux
sudo apt-get install tmux

# start new session 
tmux new-session -d -s fila_forge
tmux split-window -h


# create .env, install dependencies 
tmux send-keys -t fila_forge:0.0 '
 cd server && 
  echo "FLASK_ENV=development" > .env &&
  echo "FLASK_APP=app.py" >> .env &&
  echo "FLASK_RUN_PORT=8000" >> .env &&
  echo "SQLALCHEMY_DATABASE_URI=hvamc.db" >> .env &&
  echo "BASE_URL=http://localhost:8000" >> .env && 
  pip freeze > requirements. txt && 
  pip install -r requirements.txt && 
  flask db init &&
  flask db migrate &&
  flask db upgrade &&
' C-m
# run flask 
tmux send-keys -t fila_forge:0.0 'flask run' C-m

# split window 
tmux split-window -v

# install dependencies & run frontend 
tmux send-keys -t fila_forge:0.1 '
  cd client && 
  echo "VITE_API_ROOT=http://localhost:8000" > .env &&
  npm i &&
  npm i vite@latest &&
  npm run dev 
' Enter

echo "Script completed"
