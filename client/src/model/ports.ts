import { useRouter } from 'vue-router'
import { ref, computed, onUnmounted } from 'vue'
import * as myFetch from './myFetch'
import { toast } from './toast'
import { type Job } from './jobs'
import { socket } from './myFetch'

export function api(action: string, body?: unknown, method?: string, headers?: any) {
  headers = headers ?? {}
  return myFetch.api(`${action}`, body, method, headers).catch((err) => console.log(err))
}

export interface Device {
  device: string
  description: string
  hwid: string
  name?: string
  status?: string
  date?: Date
  id?: number
  error?: string
  queue?: Job[] //  Store job array to store queue for each printer.
  extruder_temp?: number
  bed_temp?: number
}

export function useGetPorts() {
  return {
    async ports() {
      try {
        const response = await api('getports')
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useRegisterPrinter() {
  return {
    async register(printer: Device) {
      try {
        const response = await api('register', { printer })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to register printer. Unexpected response')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to register printer. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while registering the printer')
      }
    }
  }
}

export function useRetrievePrinters() {
  return {
    async retrieve() {
      try {
        const response = await api('getprinters')
        return response.printers
      } catch (error) {
        console.error(error)
      }
    }
  }
}

// gets the printers that have threads information from the server
export function useRetrievePrintersInfo() {
  return {
    async retrieveInfo() {
      try {
        const response = await api('getprinterinfo')
        return response // return the response directly
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useSetStatus() {
  return {
    async setStatus(printerid: number | undefined, status: string) {
      try {
        const response = await api('setstatus', { printerid, status })
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useHardReset() {
  return {
    async hardReset(printerid: number | undefined) {
      try {
        const response = await api('hardreset', { printerid })
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
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useQueueRestore() {
  return {
    async queueRestore(printerid: number | undefined) {
      try {
        const response = await api('queuerestore', { printerid })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to restore queue. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to restore queue. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

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

// function needs to disconnect the socket when the component is unmounted
export function disconnectStatusSocket() {
  socket.disconnect()
}

export function setupTempSocket(printers: any) {
  socket.on('temp_update', (data: any) => {
    const printer = printers.value.find((p: Device) => p.id === data.printerid)
    if (printer) {
      printer.extruder_temp = data.extruder_temp
      printer.bed_temp = data.bed_temp
    }
  })
}
