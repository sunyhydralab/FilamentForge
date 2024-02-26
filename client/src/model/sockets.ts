import { socket } from './myFetch'
import type { Device } from './ports';

// function to set up the socket for status updates
export function setupStatusSocket(printers: any) {
  socket.on("status_update", ((data: any) => {    
    if (printers && printers.value) {
      const printer = printers.value.find((p: Device) => p.id === data.printer_id)
      if (printer) {
        printer.status = data.status;
      }
    } else {
      console.error('printers or printers.value is undefined');
    }
  }))
}

export function setupQueueSocket(printers: any) {
  socket.on("queue_update", ((data: any) => {
    if (printers && printers.value) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      console.log(printer)
      if (printer) {
        printer.queue = data.queue;
      }
    } else {
      console.error('printers or printers.value is undefined');
    }
  }
  ))
  console.log('queue socket set up')
}

export function setupErrorSocket(printers: any){
  socket.on("error_update", ((data: any) => {
    if (printers && printers.value) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      console.log(printer)
      if (printer) {
        printer.error = data.error;
      }
    } else {
      console.error('printers or printers.value is undefined');
    }
  }
  ))
  console.log('queue socket set up')
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
  // Listen for the 'job_time' event
  socket.on('job_time', (data: any) => {
    // Get the start time and total time from the server
    const job_id = data.job_id
    const total_time = data.total_time

    // Find the job with the matching id
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (!job) {
      console.error(`Job with id ${job_id} not found`)
      return
    }

    // Clear any existing timer
    if (job.timer) {
      clearInterval(job.timer)
      delete job.timer
    }

    // Set the total time for the job
    job.total_time = total_time

    // Set the start time to the current timestamp
    job.start_time = Math.floor(Date.now() / 1000)

    // Create a timer that updates the time every second
    job.timer = startTimer(job, job.start_time, 0, false) // Added fourth argument
  })

  // Listen for the 'job_pause' event
  socket.on('job_pause', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      // Calculate the elapsed time
      const pauseTime = Math.floor(Date.now() / 1000)
      job.elapsed_time = pauseTime - job.start_time

      // Update job.start_time to the pause time
      job.start_time = pauseTime

      // Pause the timer but keep incrementing the elapsed_time and total_time
      if (job.timer) {
        clearInterval(job.timer)
        job.timer = startTimer(job, job.start_time, job.elapsed_time, true)
      }
    }
  })

  // Listen for the 'job_resume' event
  socket.on('job_resume', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      // Clear any existing timer
      if (job.timer) {
        clearInterval(job.timer)
        delete job.timer
      }

      // Update job.start_time to the current timestamp
      job.start_time = Math.floor(Date.now() / 1000)

      // Start the timer
      job.timer = startTimer(job, job.start_time, job.elapsed_time, false)
    }
  })
}

function startTimer(job: any, start_time: number, elapsed_time: number, isPaused: boolean) {
  // Ensure start_time and elapsed_time are defined and are numbers
  start_time = start_time || 0
  elapsed_time = elapsed_time || 0

  return setInterval(() => {
    // Calculate the elapsed time
    let current_elapsed_time = Math.floor(Date.now() / 1000) - start_time + elapsed_time

    // Calculate the remaining time
    const remaining_time = isPaused ? job.remaining_time : job.total_time - current_elapsed_time

    // Update the job's time variables
    job.total_time = isPaused ? job.total_time + 1 : job.total_time
    job.elapsed_time = current_elapsed_time
    job.remaining_time = remaining_time

    // If the job is finished, stop the timer
    if (current_elapsed_time >= job.total_time) {
      clearInterval(job.timer)
      delete job.timer
    }
  }, 1000)
}
