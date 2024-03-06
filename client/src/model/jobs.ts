// ts file to retrieve job information
import { useRouter } from 'vue-router'
import { api } from './ports'
import { toast } from './toast'
import { type Device } from '@/model/ports'
import { onUnmounted, ref } from 'vue'
import { socket } from './myFetch'
import { saveAs } from 'file-saver'

export interface Job {
  id: number
  name: string
  file: File
  download_link?: string
  file_name_original: string
  date?: Date
  status?: string
  progress?: number //store progress of job
  printer: string //store printer name
  printerid: number
  priority?: string
  // job_id: number
  time?: {
    total?: number
    elapsed?: number
    remaining?: number
    extra?: number
    pause?: number
    eta?: Date
    timer?: NodeJS.Timeout
  }
}

export function useGetJobs() {
  return {
    async jobhistory(page: number, pageSize: number, printerIds?: number[], oldestFirst?: boolean) {
      try {
        const response = await api(
          `getjobs?page=${page}&pageSize=${pageSize}&printerIds=${JSON.stringify(printerIds)}&oldestFirst=${oldestFirst}`
        )
        return response
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the jobs')
      }
    }
  }
}

export function useAddJobToQueue() {
  return {
    async addJobToQueue(job: FormData) {
      try {
        const response = await api('addjobtoqueue', job)
        if (response) {
          return response
        } else {
          console.error('Response is undefined or null')
          return { success: false, message: 'Response is undefined or null.' }
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while adding the job to the queue')
      }
    }
  }
}

export function useAutoQueue() {
  return {
    async auto(job: FormData) {
      try {
        const response = await api('autoqueue', job)
        if (response) {
          return response
        } else {
          console.error('Response is undefined or null')
          return { success: false, message: 'Response is undefined or null.' }
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while adding the job to the queue')
      }
    }
  }
}

// function to duplicate and rerun job
export function useRerunJob() {
  return {
    async rerunJob(job: Job | undefined, printer: Device) {
      try {
        let printerpk = printer.id
        let jobpk = job?.id

        const response = await api('rerunjob', { jobpk, printerpk }) // pass rerun job the Job object and desired printer
        // const response = {"success": true, "message": "Job rerun successfully"}
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to rerun job. Unexpected response')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to rerun job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while rerunning the job')
      }
    }
  }
}

export function useRemoveJob() {
  return {
    async removeJob(job: Job | undefined) {
      let jobpk = job?.id
      try {
        const response = await api('canceljob', { jobpk })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to remove job. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to remove job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while removing the job')
      }
    }
  }
}

export function bumpJobs() {
  return {
    async bumpjob(job: Job, printer: Device, choice: number) {
      try {
        let printerid = printer.id
        let jobid = job.id
        const response = await api('bumpjob', { printerid, jobid, choice })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to bump job. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to bump job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while bumping the job')
      }
    }
  }
}

export function useReleaseJob() {
  return {
    async releaseJob(job: Job | undefined, key: number, printerId: number | undefined) {
      try {
        let jobpk = job?.id
        const response = await api('releasejob', { jobpk, key })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to release job. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to release job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while releasing the job')
      }
    }
  }
}
export function useGetGcode() {
  return {
    async getgcode(job: Job) {
      try {
        const response = await api('getgcode', job)
        return response
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the gcode')
      }
    }
  }
}

export function useGetJobFile() {
  return {
    async getFile(jobid: number) {
      try {
        const response = await api(`getfile?jobid=${jobid}`)
        const file = new Blob([response.file], { type: 'text/plain' })
        const file_name = response.file_name
        saveAs(file, file_name)
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the file')
      }
    }
  }
}

export function useClearSpace(){
  return {
    async clearSpace(){
      try {
        const response = await api('clearspace')
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to clear space. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to clear space. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

// function to constantly update progress of job
export function setupProgressSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('progress_update', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      job.progress = data.progress
      // job.elapsed_time = data.elapsed_time
      // Update the display value only if progress is defined
      if (data.progress !== undefined) {
        job.progress = data.progress
      }
    }
  })
}

export function setupJobStatusSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('job_status_update', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      job.status = data.status

      // If the job is complete, cancelled, or errored, stop the timer
      if (['complete', 'cancelled', 'error'].includes(data.status)) {
        if (job.timer) {
          clearInterval(job.timer)
          delete job.timer
        }
      }
    }
  })
}

export function setupTimeSocket(printers: any) {
  socket.on('job_time', (data: any) => {
    const job_id = data.job_id
    const total_time = data.total_time

    // Find the job and printer with the matching id
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)
    const printer = printers.find((printer: { queue: any }) =>
      printer.queue.some((job: { id: any }) => job?.id === data.job_id)
    )

    if (!job) {
      console.error(`Job with id ${job_id} not found`)
      return
    }

    if (!job.time) {
      console.log('Initializing time object')
      job.time = {
        total: 0,
        elapsed: 0,
        remaining: 0,
        extra: 0,
        pause: 0,
        eta: new Date(), // Initialize as a Date object
        timer: null
      }
    }

    job.time.total = total_time
    job.time.elapsed = 0
    job.time.remaining = total_time

    const calculateETA = (totalSeconds: number | undefined) => {
      const now = new Date()

      if (totalSeconds) {
        // Add the total time remaining (in milliseconds)
        now.setTime(now.getTime() + totalSeconds * 1000)
      }

      return now
    }

    job.time.eta = calculateETA(job.time.total)

    // Start a timer for the job
    job.time.timer = setInterval(() => {
      console.log("TOTAL: ", job.time.total)
      console.log("REMAINING: ", job.time.remaining)
      console.log("ELAPSED: ", job.time.elapsed)
      console.log("EXTRA: ", job.time.extra)
      console.log("PAUSE: ", job.time.pause)
      console.log("ETA: ", job.time.eta)
      switch (printer.status) {
        case 'printing':
          job.time.elapsed += 1
          if (job.time.elapsed > job.time.total) {
            job.time.extra += 1
            // Add the extra time to the ETA
            job.time.eta.setTime(job.time.eta.getTime() + 1000)
          } else {
            job.time.remaining -= 1
          }
          job.time.pause = 0
          break
        case 'paused':
          job.time.elapsed += 1
          job.time.total += 1
          job.time.pause += 1
          // Add the pause time to the ETA
          job.time.eta.setTime(job.time.eta.getTime() + 1000)
          // Send warning toasts and cancel the job if paused for too long
          if (job.time.pause === 600) {
            // 10 minutes
            // Send warning toast
            toast.warning('Job has been paused for 10 minutes!')
          } else if (job.time.pause === 900) {
            // 15 minutes
            // Send warning toast
            toast.warning('Job has been paused for 15 minutes!')
          } else if (job.time.pause === 1080) {
            // 18 minutes
            // Send warning toast
            toast.warning('Job has been paused for 18 minutes!')
          } else if (job.time.pause === 1200) {
            // 20 minutes
            // Send error toast and cancel the job
            toast.error('Job has been paused for 20 minutes! Cancelling job...')
          }
          break
        case 'cancelled':
        case 'error':
        case 'complete':
          clearInterval(job.time.timer)
          break
      }

      // If the job is finished, clear the timer
      if (job.time.remaining <= 0) {
        clearInterval(job.time.timer)
      }
    }, 1000) // Update every second
  })
}
