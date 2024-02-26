import { ref, computed, onUnmounted } from 'vue'
import * as myFetch from './myFetch'
import { toast } from './toast'
import { type Job } from './jobs'

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
  isExpanded?: boolean
}

export let printers = ref<Array<Device>>([]);

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

export function useSetStatus(){
  return {
    async setStatus(printerid: number | undefined, status: string){
      try {
        const response = await api('setstatus', {printerid, status})
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useHardReset(){
  return {
    async hardReset(printerid: number | undefined){
      try {
        const response = await api('hardreset', {printerid})
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

export function useQueueRestore(){
  return {
    async queueRestore(printerid: number | undefined){
      try {
        const response = await api('queuerestore', {printerid})
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
