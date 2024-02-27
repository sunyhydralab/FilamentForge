from threading import Thread
from models.printers import Printer
import serial
import serial.tools.list_ports
import time
import requests
from flask import jsonify


class PrinterThread(Thread):
    def __init__(self, printer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.printer = printer


class PrinterStatusService:
    # in order to access the app context, we need to pass the app to the PrinterStatusService, mainly for the websockets
    def __init__(self, app):
        self.app = app
        self.printer_threads = []  # array of printer threads

    def start_printer_thread(self, printer):
        # also pass the app to the printer thread
        thread = PrinterThread(
            printer, target=self.update_thread, args=(printer, self.app))
        # lets you kill the thread when the main program exits, allows for the server to be shut down
        thread.daemon = True
        thread.start()
        return thread

    def create_printer_threads(self, printers_data):
        # all printer statuses initialized to be 'online.' Instantly changes to 'ready' on initialization -- test with 'reset printer' command.
        for printer_info in printers_data:
            printer = Printer(
                id=printer_info["id"],
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
                status='configuring'
            )
            printer_thread = self.start_printer_thread(
                printer
            )  # creating a thread for each printer object
            self.printer_threads.append(printer_thread)

        # creating separate thread to loop through all of the printer threads to ping them for print status
        self.ping_thread = Thread(target=self.pingForStatus)

    # passing app here to access the app context
    def update_thread(self, printer, app):
        with app.app_context():
            while True:
                time.sleep(2)
                status = printer.getStatus()  # get printer status

                queueSize = printer.getQueue().getSize()  # get size of queue

                if (status == "ready" and queueSize > 0):
                    # wait for 2 seconds to allow the printer to process the queue
                    time.sleep(2)
                    printer.printNextInQueue()

    def resetThread(self, printer_id):
        try:
            for thread in self.printer_threads:
                if thread.printer.id == printer_id:
                    printer = thread.printer
                    thread_data = {
                        "id": printer.id,
                        "device": printer.device,
                        "description": printer.description,
                        "hwid": printer.hwid,
                        "name": printer.name
                    }
                    self.printer_threads.remove(thread)
                    self.create_printer_threads([thread_data])
                    break
            return jsonify({"success": True, "message": "Printer thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    # this method will be called by the UI to get the printers that have a threads information
    def retrieve_printer_info(self):
        printer_info_list = []
        for thread in self.printer_threads:
            printer = (
                thread.printer
            )  # get the printer object associated with the thread
            printer_info = {
                "device": printer.device,
                "description": printer.description,
                "hwid": printer.hwid,
                "name": printer.name,
                "status": printer.status,
                "id": printer.id,
                "error": printer.error,
                "queue": []  # empty queue to store job objects
            }

            queue = printer.getQueue()
            for job in queue:
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "date": job.date.strftime('%a, %d %b %Y %H:%M:%S'),
                    "printerid": job.printer_id,
                    "file_name_original": job.file_name_original,
                    "progress": job.progress,
                    "total_time": job.total_time
                }
                printer_info['queue'].append(job_info)

            printer_info_list.append(printer_info)
        return printer_info_list

    def pingForStatus(self):
        """_summary_ pseudo code
        for printer in threads:
            status = printer.getStatus()
            if status == printing:
                GCODE for print status
        """
        pass

    def getThreadArray(self):
        return self.printer_threads
