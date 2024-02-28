import { socket } from './myFetch'
import type { Device } from './ports'

// PRINTER SOCKETS

// function to set up the socket for status updates
export function setupStatusSocket(printers: any) {
  socket.on('status_update', (data: any) => {
    if (printers && printers.value) {
      const printer = printers.value.find((p: Device) => p.id === data.printer_id)
      if (printer) {
        printer.status = data.status
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupQueueSocket(printers: any) {
  socket.on('queue_update', (data: any) => {
    if (printers && printers.value) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      console.log(printer)
      if (printer) {
        printer.queue = data.queue
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
  console.log('queue socket set up')
}

export function setupErrorSocket(printers: any) {
  socket.on('error_update', (data: any) => {
    if (printers && printers.value) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      console.log(printer)
      if (printer) {
        printer.error = data.error
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
  console.log('queue socket set up')
}

// JOBS SOCKETS

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
      job.time = {
        total: 0,
        elapsed: 0,
        remaining: 0,
        timer: null
      }
    }

    job.time.total = total_time
    job.time.elapsed = 0
    job.time.remaining = total_time

    // Start a timer for the job
    job.time.timer = setInterval(() => {
      switch (printer.status) {
        case 'printing':
          job.time.elapsed += 1
          job.time.remaining -= 1
          break
        case 'paused':
          job.time.elapsed += 1
          job.time.total += 1
          break
        case 'cancelled':
        case 'error':
        case 'complete':
          clearInterval(job.timer)
          break
      }

      // If the job is finished, clear the timer
      if (job.time.remaining <= 0) {
        clearInterval(job.time.timer)
      }
    }, 1000) // Update every second
  })
}

export function setupGCodeViewerSocket(printers: any) {
  socket.on('gcode_viewer', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      // Ensure job.gcode is initialized as an array if it's not already
      if (!Array.isArray(job.gcode)) {
        job.gcode = []
      }

      // Create a new array with the new gcode
      job.gcode = [...job.gcode, data.gcode]
    }
  })
}
