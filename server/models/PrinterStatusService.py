from threading import Thread
from models.printers import Printer
import serial
import serial.tools.list_ports
import time
import requests 
# from flask import current_app


class PrinterThread(Thread):
    def __init__(self, printer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.printer = printer


class PrinterStatusService:
    def __init__(self):
        self.printer_threads = []  # array of printer threads

    def start_printer_thread(self, printer):
        thread = PrinterThread(printer, target=self.update_thread, args=(printer,)) 
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
            )
            printer_thread = self.start_printer_thread(
                printer
            )  # creating a thread for each printer object
            self.printer_threads.append(printer_thread)

        # creating separate thread to loop through all of the printer threads to ping them for print status
        self.ping_thread = Thread(target=self.pingForStatus)

    def update_thread(self, printer):  # TARGET FUNCTION
        # with current_app._get_current_object().app_context():

        while True:
            time.sleep(2)
            status = printer.getStatus()  # get printer status

            if status == "configuring":
                printer.initialize()  # code to change status from online -> ready on thread start
                
            queueSize = printer.getQueue().getSize() # get size of queue 

            # if (status == "ready" and queueSize > 0): # if something is in the queue, print next 
            #     # printer.jobDatabaseInsert(printer.getQueue().getNext()) # get next job in queue and insert into database
            #     job = printer.getQueue().getNext()
            #     # self.sendJobToDB(job)

            if (status == "ready" and queueSize > 0):
                printer.printNextInQueue()
        # this method will be called by the UI to get the printers that have a threads information

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
            }
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

