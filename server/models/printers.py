from models.db import db
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify
from Classes.Queue import Queue
import serial
import serial.tools.list_ports
import time


# model for Printer table
class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    status = None  # default setting on printer start. Runs initialization and status switches to "ready" automatically.
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    queue = Queue()
    ser = None
    currentJob = None 

    def __init__(self, device, description, hwid, name, status='configuring', id=None):
        self.device = device
        self.description = description
        self.hwid = hwid
        self.name = name
        self.status = status
        if id is not None:
            self.id = id

    # general classes
    @classmethod
    def searchByDevice(cls, hwid):
        try:
            # Query the database to find a printer by device
            printer = cls.query.filter_by(hwid=hwid).first()
            return printer is not None

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @classmethod
    def create_printer(cls, device, description, hwid, name, status):
        printerExists = cls.searchByDevice(hwid)
        if printerExists:
            return {"success": False, "message": "Printer already registered."}
        else:
            try:
                printer = cls(
                    device=device,
                    description=description,
                    hwid=hwid,
                    name=name,
                    status=status,
                )
                db.session.add(printer)
                db.session.commit()
                return {"success": True, "message": "Printer successfully registered."}
            except SQLAlchemyError as e:
                print(f"Database error: {e}")
                return (
                    jsonify({"error": "Failed to register printer. Database error"}),
                    500,
                )

    @classmethod
    def get_registered_printers(cls):
        try:
            # Query the database to get all registered printers
            printers = cls.query.all()

            # Convert the list of printers to a list of dictionaries
            printers_data = [
                {   
                    "id": printer.id,
                    "device": printer.device,
                    "description": printer.description,
                    "hwid": printer.hwid,
                    "name": printer.name,
                    "status": printer.status,
                    "date": printer.date,
                }
                for printer in printers
            ]
            # Return the list of printer information in JSON format
            return jsonify({"printers": printers_data}), 200

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to retrieve printers. Database error"}),
                500,
            )

    def setSer(self, port):
        self.ser = port

    def setStatus(self, newStatus):
        self.status = newStatus

    def connect(self):
        self.ser = serial.Serial(self.device, 115200, timeout=1)

    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.setSer(None)

    def reset(self, initializeStatus):
        self.sendGcode("G28", initializeStatus)
        self.sendGcode("G92 E0", initializeStatus)

    def parseGcode(self, file_content):
        # Read the BytesIO object into a string
        content_str = file_content.read().decode('utf-8')

        # Split the string into lines
        lines = content_str.splitlines()

        # Iterate over each line
        for line in lines:
            # Remove leading and trailing whitespace
            line = line.strip()

            # Don't send empty lines and comments. ";" is a comment in gcode.
            if len(line) == 0 or line.startswith(";"):
                continue

            # Send the line to the printer.
            self.sendGcode(line, self.ser)

    # Function to send gcode commands
    def sendGcode(self, message, initializeStatus=False):
        # Encode and send the message to the printer.
        self.ser.write(f"{message}\n".encode("utf-8"))
        # Sleep the printer to give it enough time to get the instruction.
        time.sleep(0.1)
        # Save and print out the response from the printer. We can use this for error handling and status updates.
        while True:
            response = self.ser.readline().decode("utf-8").strip()
            if "ok" in response:
                if initializeStatus == True:
                    self.setStatus("ready")
                break
            else: 
                time.sleep(2)
                if self.getStatus() == "printing":
                    # set job status to error, do a database insert. do not remove from queue. wait for user intervention. 
                    self.getCurrentJob().setStatus("error") # set status of job to error 
                    # self.jobDatabaseInsert() # If error, do not remove from queue. Insert job into DB with status "error."
                    # only remove from queue when user clicks a button on frontend to clear or mark as error.  
                self.setStatus("error")
                return
        print(f"Command: {message}, Recieved: {response}")

    def print_job(self, job):
        for line in job.gcode_lines:
            self.send_gcode(line)

    def printNextInQueue(self):
        job = self.getQueue().getNext() # get next job 
        self.setCurrentJob(job) # set current job 
        file = job.getFile()
        if self.getSer():
            job.setStatus("printing") # set job status to printing 
            self.setStatus("printing") # set printer status to printing
            self.reset(initializeStatus=False)
            self.parseGcode(file)
            self.reset(initializeStatus=False)
            self.disconnect()
            job.setStatus("complete") # set job status to complete 
            # HERE: PERFORM DATABASE INSERT OF JOB DATA INTO JOB HISTORY TABLE
            self.setStatus("complete")
            # WHEN THE USER CLEARS THE JOB: remove job from queue, set printer status to ready, and set current job to None. 
        else:
            raise Exception(
                "Failed to establish serial connection for printer: ", self.name
            )

    def initialize(self):
        self.ser = serial.Serial(
            self.getDevice(), 115200, timeout=1
        )  # set up serial communication
        if self.getSer():
            self.reset(initializeStatus=True)
        else:
            raise Exception(
                "Failed to establish serial connection for printer: ", self.name
            )

    def jobDatabaseInsert(self):
        job = self.getCurrentJob()
        job.jobHistoryInsert(job.getFile(), job.getName(), job.getPrinterId(), job.getStatus())
        # print("STATUS: ", job.getStatus())
        
    # printer-specific classes
    def getDevice(self):
        return self.device

    def getQueue(self):
        return self.queue

    def getStatus(self):
        return self.status

    def getName(self):
        return self.name

    def getSer(self):
        return self.ser
    
    def getId(self):
        return self.id
    
    def setCurrentJob(self, job):
        self.currentJob = job
        
    def getCurrentJob(self): 
        return self.currentJob