from flask import Blueprint, jsonify
from app import printer_status_service  # import the instance from app.py
from flask import Blueprint, jsonify, request
from models.jobs import Job 

status_bp = Blueprint("status", __name__)

@status_bp.route('/ping', methods=["GET"])
def getStatus(Printer):
    pass

@status_bp.route('/getopenthreads')
def getOpenThreads():
    pass 

# this is the route that will be called by the UI to get the printers that have threads information
@status_bp.route('/getprinterinfo', methods=["GET"])
def getPrinterInfo():
    try: 
        printer_info = printer_status_service.retrieve_printer_info()  # call the method on the instance
        return jsonify(printer_info)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@status_bp.route('/hardreset', methods=["POST"])
def hardreset():
    try: 
        data = request.get_json() # get json data 
        id = data['printerid']
        res = printer_status_service.resetThread(id)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

    
@status_bp.route("/queuerestore", methods=["POST"])
def queueRestore():
    try:
        data = request.get_json() # get json data
        printerid = data['printerid']
        res = Job.queueRestore(printerid)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/removethread", methods=["POST"])
def removeThread():
    try:
        data = request.get_json() # get json data
        printerid = data['printerid']
        res = printer_status_service.deleteThread(printerid)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/editNameInThread", methods=["POST"])
def editName(): 
    try: 
        data = request.get_json() 
        printerid = data['printerid']
        name = data['newname']
        print(name)
        res = printer_status_service.editName(printerid, name)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    