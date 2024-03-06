# get connected serial ports
import serial
import serial.tools.list_ports
import time
from flask_cors import cross_origin
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify, request, make_response
from models.printers import Printer
# from models.jobs import Job
# from models.PrinterStatusService import PrinterStatusService
# from app import printer_status_service

ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports",  methods=["GET"])
def getPorts():
    printerList = Printer.getConnectedPorts()
    return jsonify(printerList)

# method to get printers already registered with the system 
@ports_bp.route("/getprinters", methods=["GET"])
def getRegisteredPrinters():  
    try: 
        res = Printer.get_registered_printers()
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@ports_bp.route("/register", methods=["POST"])
def registerPrinter(): 
    try: 
        from app import printer_status_service
        data = request.get_json() # get json data 
        # extract data 
        device = data['printer']['device']
        description = data['printer']['description']
        hwid = data['printer']['hwid']
        name = data['printer']['name']
        
        res = Printer.create_printer(device=device, description=description, hwid=hwid, name=name, status='ready')
        if(res["success"] == True):
            id = res['printer_id']
                    
            thread_data = {
                "id": id, 
                "device": device,
                "description": description,
                "hwid": hwid,
                "name": name
            }
            
            printer_status_service.create_printer_threads([thread_data])
        
        return res
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@ports_bp.route("/deleteprinter", methods=["POST"])
def delete_printer():
    try: 
        data = request.get_json()
        printerid = data['printerid']
        # res = printer_status_service.deleteThread(printerid)
        res = Printer.deletePrinter(printerid)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@ports_bp.route("/editname", methods=["POST"])
def edit_name(): 
    try: 
        data = request.get_json() 
        printerid = data['printerid']
        name = data['name']
        res = Printer.editName(printerid, name)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@ports_bp.route("/diagnose", methods=["POST"])
def diagnose_printer():
    try:
        data = request.get_json() 
        device = data['device']
        res = Printer.diagnosePrinter(device)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
