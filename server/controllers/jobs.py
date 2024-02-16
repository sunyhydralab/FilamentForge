from io import BytesIO
from flask import Blueprint, jsonify, request, make_response
from models.jobs import Job
from models.printers import Printer
from app import printer_status_service
import json 
from werkzeug.utils import secure_filename
import os 
# get data for jobs 
jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route('/getjobs', methods=["GET"])
def getJobs():
    page = request.args.get('page', default=1, type=int)
    pageSize = request.args.get('pageSize', default=10, type=int)
    printerIds = request.args.get('printerIds', type=json.loads)
    try:
        res = Job.get_job_history(page, pageSize, printerIds)
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

# add job to queue
@jobs_bp.route('/addjobtoqueue', methods=["POST"])
def add_job_to_queue():
    try:
        # retrieve job data 
        file = request.files['file']  # Access file directly from request.files
        file_name_original = file.filename
        
        name = request.form['name']  # Access other form fields from request.form
        printer_id = int(request.form['printerid'])
        # quantity = int(request.form['quantity'])
        
        status = 'inqueue' # set status 
        res = Job.jobHistoryInsert(name, printer_id, status, file, file_name_original) # insert into DB 
        
        # retrieve job from DB
        id = res['id']
        
        job = Job.query.get(id)
        
        file_name_pk = file_name_original + f"_{id}" # append id to file name to make it unique
        
        job.setFileName(file_name_pk) # set unique in-memory file name 

        findPrinterObject(printer_id).getQueue().addToBack(job)
        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@jobs_bp.route('/rerunjob', methods=["POST"])
def rerun_job():
    try:
        data = request.get_json()
        printerpk = data['printerpk'] # printer to rerun job on 
        jobpk = data['jobpk']
        
        rerunjob(printerpk, jobpk, "back")
        # job = Job.findJob(jobpk) # retrieve Job to rerun 
        
        # status = 'inqueue' # set status 
        # file_name_original = job.getFileNameOriginal() # get original file name
        
        # # Insert new job into DB and return new PK 
        # res = Job.jobHistoryInsert(name=job.getName(), printer_id=printerpk, status=status, file=job.getFile(), file_name_original=file_name_original) # insert into DB 
        
        # id = res['id']
        # file_name_pk = file_name_original + f"_{id}" # append id to file name to make it unique
        
        # rerunjob = Job.query.get(id)
        
        # file_name_pk = file_name_original + f"_{id}" # append id to file name to make it unique
        # rerunjob.setFileName(file_name_pk) # set unique file name 
        
        # findPrinterObject(printerpk).getQueue().addToBack(rerunjob)

        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
# route to insert job into database
@jobs_bp.route('/jobdbinsert', methods=["POST"])
def job_db_insert():
    try:
        jobdata = request.form.get('jobdata')
        
        jobdata = json.loads(jobdata)  # Convert jobdata from JSON to a Python dictionary

        # Get the individual fields from jobdata
        name = jobdata.get('name')
        printer_id = jobdata.get('printer_id')
        status = jobdata.get('status')
        # file_name=jobdata.get("file_name")
        file_path=jobdata.get("file_path")

        # Insert the job data into the database
        res = Job.jobHistoryInsert(name, printer_id, status, file_path)

        return "success"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
 
 # cancel queued job   
@jobs_bp.route('/canceljob', methods=["POST"]) 
def remove_job():
    try:
        # job has: printer id. job info.
        # 0 = cancel job, 1 = clear job, 2 = fail job, 3 = clear job (but also rerun)
        data = request.get_json()
        jobpk = data['jobpk']
        

        # Retrieve job to delete & printer id 
        job = Job.findJob(jobpk) 
        printerid = job.getPrinterId() 

        jobstatus = job.getStatus()

        # retrieve printer object & corresponding queue
        printerobject = findPrinterObject(printerid)
        # printerobject.setStatus("complete")
        queue = printerobject.getQueue()

        # if jobstatus == 'printing': # only change statuses, dont remove from queue 
        #     printerobject.setStatus("complete")
        # else: 
        queue.deleteJob(jobpk) 
            
        job.setStatus("cancelled")
        Job.update_job_status(jobpk, "cancelled")

        return jsonify({"success": True, "message": "Job removed from printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/releasejob', methods=["POST"])
def releasejob(): 
    try: 
        data = request.get_json()
        jobpk = data['jobpk']
        key = data['key']
        job = Job.findJob(jobpk) 
        printerid = job.getPrinterId() 
        printerobject = findPrinterObject(printerid)
        queue = printerobject.getQueue()

        queue.deleteJob(jobpk) # remove job from queue 

        if key == 3: 
            Job.update_job_status(jobpk, "error")
            printerobject.setStatus("error") # printer ready to accept new prints 
        elif key == 2: 
            rerunjob(printerid, jobpk, "front")
            printerobject.setStatus("ready") # printer ready to accept new prints 
        elif key == 1: 
            printerobject.setStatus("ready") # printer ready to accept new prints 
        return jsonify({"success": True, "message": "Job released successfully."}), 200
    except Exception as e: 
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500  
    
@jobs_bp.route('/bumpjob', methods=["POST"])
def bumpjob():
    try:
        data = request.get_json()
        printer_id = data['printerid']
        job_id = data['jobid']
        choice = data['choice']
        
        printerobject = findPrinterObject(printer_id)
        
        if choice == 1: 
            printerobject.queue.bump(True, job_id)
        elif choice == 2: 
            printerobject.queue.bump(False, job_id)
        elif choice == 3: 
            printerobject.queue.bumpExtreme(True, job_id)
        elif choice == 4: 
            printerobject.queue.bumpExtreme(False, job_id)
        else: 
            return jsonify({"error": "Unexpected error occurred"}), 500
        
        return jsonify({"success": True, "message": "Job bumped up in printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/updatejobstatus', methods=["POST"])
def updateJobStatus():
    try:
        data = request.get_json()
        job_id = data['jobid']
        newstatus = data['status']
        
        res = Job.update_job_status(job_id, newstatus)
        
        return jsonify(res), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@jobs_bp.route("/setstatus", methods=["POST"])
def setStatus():
    try:
        data = request.get_json() # get json data 
        printer_id = data['printerid']
        newstatus = data['status']
 
        printerobject = findPrinterObject(printer_id)
        
        printerobject.setStatus(newstatus)
        
        return jsonify({"success": True, "message": "Status updated successfully."}), 200

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
def findPrinterObject(printer_id): 
    threads = printer_status_service.getThreadArray()
    return list(filter(lambda thread: thread.printer.id == printer_id, threads))[0].printer  

def rerunjob(printerpk, jobpk, position):
    job = Job.findJob(jobpk) # retrieve Job to rerun 
    
    status = 'inqueue' # set status 
    file_name_original = job.getFileNameOriginal() # get original file name
    
    # Insert new job into DB and return new PK 
    res = Job.jobHistoryInsert(name=job.getName(), printer_id=printerpk, status=status, file=job.getFile(), file_name_original=file_name_original) # insert into DB 
    
    id = res['id']
    file_name_pk = file_name_original + f"_{id}" # append id to file name to make it unique
    
    rjob = Job.query.get(id)
    
    base_name, extension = os.path.splitext(file_name_original)

    # Append the ID to the base name
    file_name_pk = f"{base_name}_{id}{extension}"
    
    rjob.setFileName(file_name_pk) # set unique file name 
    
    if position == "back":
        findPrinterObject(printerpk).getQueue().addToBack(rjob)
    else: 
        findPrinterObject(printerpk).getQueue().addToFront(rjob)