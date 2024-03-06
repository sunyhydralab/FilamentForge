from collections import deque
from flask import jsonify, current_app
class Queue: 
    # Only adding ID to the queue 
    def __init__(self):
        self.__queue = deque() # use Python double-ended queue  
            
    def __iter__(self): # iterate over queue 
        return iter(self.__queue)
    
    # if no priority add to end of queue. If priority add to front of queue. 
    def addToBack(self, job, printerid):
        if self.__queue.count(job)>0: 
            raise Exception("Job ID already in queue.") 
        self.__queue.append(job) # appending on the right is the "front" because popping takes out from right d
        current_app.socketio.emit('queue_update', {'queue': self.convertQueueToJson(), 'printerid': printerid})

    
    def addToFront(self, job, printerid): 
        if self.__queue.count(job)>0: 
            raise Exception("Job ID already in queue.") 
        # If the queue has at least one job and the first job is printing,
        # insert at the second position because we don't want to interrupt it.
        if len(self.__queue) >= 1 and self.__queue[0].status == 'printing':
            self.__queue.insert(1, job)
        # If the queue is empty or the first job is not printing,
        # add the job to the front
        else:
            self.__queue.appendleft(job)
        current_app.socketio.emit('queue_update', {'queue': self.convertQueueToJson(), 'printerid': printerid})

    
    def bump(self, up, jobid): # up = boolean. if up = true bump up, else bump down 
        index = next((index for index, queued_job in enumerate(self.__queue) if queued_job.id == jobid), -1)
        if index == -1:
            print("Job not found in queue.")
            return
        job_to_move = self.__queue[index]
        self.__queue.remove(job_to_move)
        if up==True and index > 0: 
            self.__queue.insert(index-1, job_to_move)
        elif not up and index < len(self.__queue): 
            self.__queue.insert(index+1, job_to_move)
    
    def deleteJob(self, jobid, printerid):
        deletedjob = None
        for job in self.__queue:
            if job.getJobId() == jobid:
                deletedjob = job
                self.__queue.remove(job)
                current_app.socketio.emit('queue_update', {'queue': self.convertQueueToJson(), 'printerid': printerid})
                return deletedjob
            
    def convertQueueToJson(self):
        queue = []
        # job_info = {}
        for job in self.__queue: 
            job_info = {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "date": job.date.strftime('%a, %d %b %Y %H:%M:%S'),
                "printerid": job.printer_id, 
                "file_name_original": job.file_name_original
            }
            queue.append(job_info)    
        return queue 
    
    def bumpExtreme(self, front, jobid, printerid): # bump to back/front of queue 
        index = next((index for index, queued_job in enumerate(self.__queue) if queued_job.id == jobid), -1)
        if index == -1:
            print("Job not found in queue.")
            return
        job_to_move = self.__queue[index]
        self.__queue.remove(job_to_move)
        if front == True:
            # If the queue has at least one job and the first job is printing,
            # insert at the second position because we don't want to interrupt it.
            if len(self.__queue) >= 1 and self.__queue[0].status == 'printing':
                self.__queue.insert(1, job_to_move)
            # If the queue is empty or the first job is not printing,
            # add the job to the front
            else:
                self.__queue.insert(0, job_to_move)
        else: 
            self.addToBack(job_to_move, printerid)
            
    
    def getJob(self, job_to_find):
        for job in self.__queue:
            if job.getJobId() == job_to_find.getJobId():
                return job
        return None  # Return None if job is not found in the queue
    
    def jobExists(self, jobid):
        for job in self.__queue:
            if job.id == jobid:
                return True
        return False
        
         
    def getQueue(self): 
        return self.__queue
    
    def getNext(self): 
        return self.__queue[0]
    
    def getSize(self): 
        return len(self.__queue)
    
    def removeJob(self):
        self.__queue.pop()
        # current_app.socketio.emit('job_removed', {'queue': list(self.__queue)}, broadcast=True)


    
    

