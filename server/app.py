from flask import Flask, jsonify, request, Response, url_for
from threading import Thread
from flask_cors import CORS 
import os 
from models.db import db
from models.printers import Printer
from models.PrinterStatusService import PrinterStatusService
from flask_migrate import Migrate
from dotenv import load_dotenv
from controllers.ports import getRegisteredPrinters
import shutil
from flask_socketio import SocketIO
from datetime import datetime, timedelta
from sqlalchemy import text
# moved this up here so we can pass the app to the PrinterStatusService
# Basic app setup 
app = Flask(__name__)
app.config.from_object(__name__) # update application instantly 

# moved this before importing the blueprints so that it can be accessed by the PrinterStatusService
printer_status_service = PrinterStatusService(app)

# Initialize SocketIO, which will be used to send printer status updates to the frontend
# and this specific socketit will be used throughout the backend
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False, socketio_logger=False, async_mode='threading') # Initialize SocketIO with the Flask app
app.socketio = socketio  # Add the SocketIO object to the app object

# IMPORTING BLUEPRINTS 
from controllers.display import display_bp
from controllers.ports import ports_bp
from controllers.jobs import jobs_bp
from controllers.statusService import status_bp, getStatus 

CORS(app)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        return res

# start database connection
load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
database_file = os.path.join(basedir, os.environ.get('SQLALCHEMY_DATABASE_URI'))
database_uri = 'sqlite:///' + database_file
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

migrate = Migrate(app, db)

# # Register the display_bp Blueprint
app.register_blueprint(display_bp)
app.register_blueprint(ports_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(status_bp)

# own thread
with app.app_context():
    try:
        # Creating printer threads from registered printers on server start 
        res = getRegisteredPrinters() # gets registered printers from DB 
        data = res[0].get_json() # converts to JSON 
        printers_data = data.get("printers", []) # gets the values w/ printer data
        printer_status_service.create_printer_threads(printers_data)
        
        # Create in-memory uploads folder 
        uploads_folder = os.path.join('../uploads')
        if os.path.exists(uploads_folder):
            # Remove the uploads folder and all its contents
            shutil.rmtree(uploads_folder)
            # Recreate it as an empty directory
            os.makedirs(uploads_folder)
            print("Uploads folder recreated as an empty directory.")
        else:
            # Create the uploads folder if it doesn't exist
            os.makedirs(uploads_folder)
            print("Uploads folder created successfully.")  
    except Exception as e:
        print(f"Unexpected error: {e}")
            

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    # since we are using socketio, we need to use socketio.run instead of app.run
    # which passes the app anyways
    socketio.run(app, port=8000, debug=True)  # Replace app.run with socketio.run