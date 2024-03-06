import asyncio
import re
from models.db import db
from datetime import datetime, timezone
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, current_app
from Classes.Queue import Queue
import serial
import serial.tools.list_ports
import time
from tzlocal import get_localzone
import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

# model for Printer table


class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(
        timezone.utc).astimezone(), nullable=False)
    queue = None
    ser = None
    # default setting on printer start. Runs initialization and status switches to "ready" automatically.
    status = None
    # stopPrint = False
    responseCount = 0  # if count == 10 & no response, set error
    error = ""
    extruder_temp = 0
    bed_temp = 0

    def __init__(self, device, description, hwid, name, status=status, id=None):
        self.device = device
        self.description = description
        self.hwid = hwid
        self.name = name
        self.status = status
        self.date = datetime.now(get_localzone())
        self.queue = Queue()
        self.stopPrint = False
        self.error = ""
        self.extruder_temp = 0
        self.bed_temp = 0

        if id is not None:
            self.id = id
        self.responseCount = 0

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
        try:
            printerExists = cls.searchByDevice(hwid)
            if printerExists:
                printer = cls.query.filter_by(hwid=hwid).first()
                return {"success": False, "message": f"Port already registered under hwid: {printer.name}."}
            else:
                printer = cls(
                    device=device,
                    description=description,
                    hwid=hwid,
                    name=name,
                    status=status,
                )
                db.session.add(printer)
                db.session.commit()
                return {"success": True, "message": "Printer successfully registered.", "printer_id": printer.id}
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
                    # Include timezone abbreviation
                    "date": f"{printer.date.strftime('%a, %d %b %Y %H:%M:%S')} {get_localzone().tzname(printer.date)}",
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

    @classmethod
    def getConnectedPorts(cls):
        ports = serial.tools.list_ports.comports()
        printerList = []
        for port in ports:
            port_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
            }
            # supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
            # if port.description in supportedPrinters:
            printerList.append(port_info)
        return printerList
    
    @classmethod 
    def diagnosePrinter(cls, deviceToDiagnose): # deviceToDiagnose = port 
        try: 
            diagnoseString = ''
            ports = serial.tools.list_ports.comports()
            for port in ports: 
                if port.device == deviceToDiagnose:
                    diagnoseString += f"The system has found a matching port with the following details: <br><br> Device: {port.device}, <br> Description: {port.description}, <br> HWID: {port.hwid}<br><br>"
                    printerExists = cls.searchByDevice(port.hwid)
                    if(printerExists):
                        printer = cls.query.filter_by(hwid=port.hwid).first()
                        diagnoseString += f"Device {port.device} is registered with the following details: <br><br> Name: {printer.name} <br> Device: {printer.device}, <br> Description: {printer.description}, <br> HWID: {printer.hwid}<br><br>"
            if diagnoseString == '':
                diagnoseString = "The port this printer is registered under is not found. Please check the connection and try again."
            # return diagnoseString
            return {"success": True, "message": "Printer successfully diagnosed.", "diagnoseString": diagnoseString}

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500
                
    @classmethod 
    def findPrinter(cls, id):
        try:
            printer = cls.query.get(id)
            return printer
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to retrieve printer. Database error"}),
                500,
            )
            
    @classmethod 
    def deletePrinter(cls, printerid):
        try:   
            printer = cls.query.get(printerid)
            db.session.delete(printer)
            db.session.commit()
            return {"success": True, "message": "Printer successfully deleted."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to delete printer. Database error"}),
                500,
            )
            
    @classmethod
    def editName(cls, printerid, name):
        try:
            printer = cls.query.get(printerid)
            printer.name = name
            db.session.commit()
            return {"success": True, "message": "Printer name successfully updated."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to update printer name. Database error"}),
                500,
            )

    def connect(self):
        try: 
            self.ser = serial.Serial(self.device, 115200, timeout=1)
            self.ser.write(f"M155 S5\n".encode("utf-8"))
        except Exception as e: 
            self.setError(e)
            return "error"

    def disconnect(self):
        if self.ser:
            self.ser.write(f"M155 S0\n".encode("utf-8"))
            self.ser.close()
            self.setSer(None)

    def reset(self):
        self.sendGcode("G28")
        self.sendGcode("G92 E0")

    # Function to send gcode commands
    def sendGcode(self, message, job):
        try:
            # Encode and send the message to the printer.
            self.ser.write(f"{message}\n".encode("utf-8"))
            # Sleep the printer to give it enough time to get the instruction.
            # time.sleep(0.1)
            # Save and print out the response from the printer. We can use this for error handling and status updates.
            while True:
                print("in send")
                # logic here about time elapsed since last response
                response = self.ser.readline().decode("utf-8").strip()

                if response == "":
                    self.responseCount += 1
                    if (self.responseCount >= 10):
                        self.setError("No response from printer")
                        raise Exception("No response from printer")
                elif "error" in response.lower():
                    self.setError(response)
                    break
                else:
                    self.responseCount = 0

                if ("M190" in message or "M109" in message) and job.time_started is False:
                    # Send the line M155 S5 to the printer to ping for temperature every 5 seconds
                    print("STARTING TIMER")
                    job.time_started = True
                    job.startTimer()

                if ("T:" in response) and ("B:" in response):
                    # Extract the temperature values using regex
                    temp_t = re.search(r'T:(\d+.\d+)', response)
                    temp_b = re.search(r'B:(\d+.\d+)', response)
                    if temp_t and temp_b:
                        self.setTemps(temp_t.group(1), temp_b.group(1))

                stat = self.getStatus()
                if stat == "complete" or stat == "error":
                    break

                if "ok" in response:
                    break

                print(f"Command: {message}, Received: {response}")
        except Exception as e:
            print("exception in sendGcode")
            self.setError(e)
            return "error"

    def gcodeEnding(self, message):
        try:
            # Encode and send the message to the printer.
            self.ser.write(f"{message}\n".encode("utf-8"))
            # Sleep the printer to give it enough time to get the instruction.
            # time.sleep(0.1)
            # Save and print out the response from the printer. We can use this for error handling and status updates.
            while True:
                # logic here about time elapsed since last response
                response = self.ser.readline().decode("utf-8").strip()
                
                if response == "":
                    self.responseCount+=1 
                    if(self.responseCount>=10):
                        self.setError("No response from printer")
                        raise Exception("No response from printer")
                elif "error" in response.lower():
                    self.setError(response)
                    break
                else:
                    self.responseCount = 0
                    
                stat = self.getStatus()
                
                if stat != "complete":
                    break 
                
                if "ok" in response:
                    break
                print(f"Command: {message}, Received: {response}")
        except Exception as e:
            # self.setStatus("error")
            print(e)
            self.setError(e)
            return "error"

    def parseGcode(self, path, job):
        try:
            with open(path, "r") as g:
                # Read the file and store the lines in a list

                lines = g.readlines()

                #  Time handling
                comment_lines = [
                    line for line in lines if line.strip() and line.startswith(";")]
                time_seconds = job.getTimeSeconds(comment_lines)
                job.total_time = time_seconds

                # Only send the lines that are not empty and don't start with ";"
                # so we can correctly get the progress
                command_lines = [
                    line for line in lines if line.strip() and not line.startswith(";")]
                # store the total to find the percentage later on
                total_lines = len(command_lines)
                # set the sent lines to 0
                sent_lines = 0

                # Replace file with the path to the file. "r" means read mode.
                # now instead of reading from 'g', we are reading line by line
                for line in lines:
                    # remove whitespace
                    line = line.strip()
                    # Don't send empty lines and comments. ";" is a comment in gcode.
                    if ";" in line:  # Remove inline comments
                        # Remove comments starting with ";"
                        line = line.split(";")[0].strip()
                    if len(line) == 0 or line.startswith(";"):
                        continue
                    # Send the line to the printer.
                    # time.sleep(1)
                    if (self.getStatus() == "paused" or ("M601" in line) or ("M0" in line)):
                        self.setStatus("paused")
                        # set relative positioning mode
                        # self.sendGcode("G91", job)
                        # self.sendGcode("G1 Z10 F300", job)  # move up 10mm
                        # self.sendGcode("M601", job) # pause command
                        self.sendGcode("M600", job) # change filament command
                        # self.sendGcode("G1 Z-10 F300")
                        pause_time = time.time()  # get the current time
                        while (True):
                            stat = self.getStatus()
                            if (stat == "printing"):
                                # move back to previous position
                                # self.sendGcode("G1 Z-10 F300", job)
                                # # set back to absolute positioning
                                # self.sendGcode("G90", job)
                                # self.sendGcode("M602", job)  # pause resume command
                                break
                            elif time.time() - pause_time > 1200:  # 20 minutes * 60 seconds
                                return "paused_too_long"

                    # right now, if pause is in the line, M601 will be sent twice to avoid duplicate code.
                    # test to see if thatll be an issue.

                    res = self.sendGcode(line, job)

                    # if("M601" in line):
                    #     self.setStatus("paused")
                    #     while(True):
                    #         stat = self.getStatus()
                    #         if(stat=="printing"):
                    #             break

                    # Increment the sent lines
                    sent_lines += 1
                    # Calculate the progress
                    progress = (sent_lines / total_lines) * 100

                    # Call the setProgress method
                    job.setProgress(progress)
                    
                    
                    if self.getStatus() == "complete":
                        return "cancelled"

                    if self.getStatus() == "error":
                        return "error"

            return "complete"
        except Exception as e:
            # self.setStatus("error")
            self.setError(e)
            return "error"

    # Function to send "ending" gcode commands
    def endingSequence(self):
        try:
            # *** Ender 3 Pro ending sequence ***
            self.gcodeEnding("G91")  # Relative positioning
            self.gcodeEnding("G1 E-2 F2700")  # Retract a bit
            self.gcodeEnding("G1 E-2 Z0.2 F2400")  # Retract and raise Z
            self.gcodeEnding("G1 X5 Y5 F3000")  # Wipe out
            self.gcodeEnding("G1 Z10")  # Raise Z more
            self.gcodeEnding("G90")  # Absolute positioning
            self.gcodeEnding("G1 X0 Y220")  # Present print
            self.gcodeEnding("M106 S0")  # Turn-off fan
            self.gcodeEnding("M104 S0")  # Turn-off hotend
            self.gcodeEnding("M140 S0")  # Turn-off bed
            self.gcodeEnding("M84 X Y E")  # Disable all steppers but Z

            # *** Prusa i3 MK3 ending sequence ***
            # self.gcodeEnding("M104 S0") # turn off extruder
            # self.gcodeEnding("M140 S0") # turn off heatbed
            # self.gcodeEnding("M107") # turn off fan
            # self.gcodeEnding("G91") # relative positioning
            # self.gcodeEnding("G1 Z10 F3000") # move Z up
            # self.gcodeEnding("G90") # absolute positioning
            # self.gcodeEnding("G1 X0 Y210") # home X axis and push Y forward
            # self.gcodeEnding("M84") # disable motors

            # *** Prusa MK4 ending sequence ***
            # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+1, max_print_height)} F720 {endif}") # Move print head up
            # self.gcodeEnding("M104 S0") # turn off temperature
            # self.gcodeEnding("M140 S0") # turn off heatbed
            # self.gcodeEnding("M107") # turn off fan
            # self.gcodeEnding("G1 X241 Y170 F3600") # park
            # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+23, max_print_height)} F300 {endif}") # Move print head up
            # self.gcodeEnding("G4") # wait
            # self.gcodeEnding("M900 K0") # reset LA
            # self.gcodeEnding("M142 S36") # reset heatbreak target temp
            # self.gcodeEnding("M84 X Y E") # disable motors

        except Exception as e:
            self.setError(e)
            return "error"

    def printNextInQueue(self):
        self.connect()
        job = self.getQueue().getNext()  # get next job
        try:
            if self.getSer():
                job.saveToFolder()
                path = job.generatePath()

                self.setStatus("printing")  # set printer status to printing
                self.sendStatusToJob(job, job.id, "printing")

                verdict = self.parseGcode(path, job) # passes file to code. returns "complete" if successful, "error" if not.
                
                if verdict =="complete":
                    self.disconnect()
                    self.setStatus("complete")
                    self.sendStatusToJob(job, job.id, "complete")
                elif verdict == "error":
                    self.disconnect()
                    self.getQueue().deleteJob(job.id, self.id)
                    self.setStatus("error")
                    self.sendStatusToJob(job, job.id, "error")
                elif verdict == "cancelled":
                    self.endingSequence()
                    self.disconnect()
                    self.sendStatusToJob(job, job.id, "cancelled")
                elif verdict == "paused_too_long":
                    self.endingSequence()
                    self.disconnect()
                    self.setStatus("complete")
                    self.sendStatusToJob(job, job.id, "cancelled")
                else:
                    self.disconnect()

                # remove file from folder after job complete
                job.removeFileFromPath(path)
            # WHEN THE USER CLEARS THE JOB: remove job from queue, set printer status to ready.
            else:
                self.getQueue().deleteJob(job.id, self.id)
                # self.setStatus("error")
                self.setError("Printer not connected")
                self.sendStatusToJob(job, job.id, "error")
            return     
        except Exception as e:
            # print("exception in printNextInQueue except")
            self.getQueue().deleteJob(job.id, self.id)
            # self.setStatus("error")
            self.sendStatusToJob(job, job.id, "error")
            self.setError(e)

    def fileExistsInPath(self, path):
        if os.path.exists(path):
            return True

    # printer-specific classes
    def getDevice(self):
        return self.device

    def getQueue(self):
        return self.queue

    # def removeJobFromQueue(self, job_id):
    #     self.queue.removeJob(job_id)

    #     current_app.socketio.emit('job_removed', {'printer_id': self.id, 'job_id': job_id})

    def getStatus(self):
        return self.status

    def getName(self):
        return self.name

    def getSer(self):
        return self.ser

    def getId(self):
        return self.id

    def getStopPrint(self):
        return self.stopPrint

    def setSer(self, port):
        self.ser = port

    #  now when we set the status, we can emit the status to the frontend
    def setStatus(self, newStatus):
        try:
            self.status = newStatus 
            # print(self.status)
            # Emit a 'status_update' event with the new status
            current_app.socketio.emit(
                'status_update', {'printer_id': self.id, 'status': newStatus})
        except Exception as e:
            print('Error setting status:', e)

    def setStopPrint(self, stopPrint):
        self.stopPrint = stopPrint

    def setError(self, error):
        self.error = str(error) 
        self.setStatus("error")
        current_app.socketio.emit(
            'error_update', {'printerid': self.id, 'error': self.error})

    def sendStatusToJob(self, job, job_id, status):
        try:
            job.setStatus(status)
            data = {
                "printerid": self.id,
                "jobid": job_id,
                "status": status  # Assuming status is accessible here
            }
            base_url = os.getenv("BASE_URL", "http://localhost:8000")

            response = requests.post(f"{base_url}/updatejobstatus", json=data)
            if response.status_code == 200:
                print("Status sent successfully")
            else:
                print("Failed to send status:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send status to job: {e}")

    def setTemps(self, extruder_temp, bed_temp):
        self.extruder_temp = extruder_temp
        self.bed_temp = bed_temp
        current_app.socketio.emit(
            'temp_update', {'printerid': self.id, 'extruder_temp': self.extruder_temp, 'bed_temp': self.bed_temp})
