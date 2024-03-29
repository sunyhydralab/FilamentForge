# get connected serial ports
import serial
import serial.tools.list_ports
import time
from flask_cors import cross_origin
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify, request, make_response
from models.printers import Printer

ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports",  methods=["GET"])
def getPorts():
    ports = serial.tools.list_ports.comports()
    printerList = []
    for port in ports:
        port_info = {
            'device': port.device,
            'description': port.description,
            'hwid': port.hwid,
        }
        supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
        # if port.description in supportedPrinters:
        printerList.append(port_info)
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
    """_summary
    interface RegisteredDevice {
        device: string; 
        description: string; 
        hwid: string; 
        customname: string; 
    }
    """
    try: 
        data = request.get_json() # get json data 
        # extract data 
        device = data['printer']['device']
        description = data['printer']['description']
        hwid = data['printer']['hwid']
        name = data['printer']['name']
        
        res = Printer.create_printer(device=device, description=description, hwid=hwid, name=name, status='ready')
        return res
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
        
# method to get the queue for a printer
# unsure if this works tbh, need help!
@ports_bp.route("/getqueue", methods=["GET"])
def getQueue(printer_name):
    try:
        # Query the database to find the printer by name
        printer = Printer.query.get(printer_name)
        if printer is None:
            return jsonify({'error': 'Printer not found'}), 404
        queue = printer.queue.getQueue()
        return jsonify({'queue': queue}), 200

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to retrieve queue. Database error"}), 500