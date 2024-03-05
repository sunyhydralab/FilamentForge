<script setup lang="ts">
import { useRetrievePrintersInfo, useSetStatus, setupStatusSocket, setupQueueSocket, setupErrorSocket, disconnectStatusSocket, type Device, setupTempSocket } from '@/model/ports';
import { type Job, useReleaseJob, useRemoveJob, setupProgressSocket, setupJobStatusSocket, setupTimeSocket } from '@/model/jobs';
import { useRouter, useRoute } from 'vue-router';
import { onMounted, onUnmounted, ref, watch } from 'vue';

const { retrieveInfo } = useRetrievePrintersInfo();
const { setStatus } = useSetStatus();
const { releaseJob } = useReleaseJob()
const { removeJob } = useRemoveJob()

const router = useRouter();

let printers = ref<Array<Device>>([]); // Array of all devices. Used to list registered printers on frontend. 
// ref of a current job. Used to display the job details in the modal
let currentJob = ref<Job>();
let currentPrinter = ref<Device>();

let intervalId: number | undefined;

onMounted(async () => {
  try {

    printers.value = await retrieveInfo()
    // const route = useRoute()
    // const printerName = route.params.printerName
    // const updatePrinters = async () => {
    //   const printerInfo = await retrieveInfo()
    //   printers.value = []
    //   for (const printer of printerInfo) {
    //     printers.value.push({
    //       ...printer,
    //       isExpanded: printer.name === printerName
    //     })
    //   }
    // }
    // Fetch the printer status immediately on mount
    // await updatePrinters()
    // Setup the satus socket
    setupStatusSocket(printers)

    setupQueueSocket(printers)
    // Setup the progress socket
    setupProgressSocket(printers.value)

    setupJobStatusSocket(printers.value)

    setupErrorSocket(printers)

    setupTimeSocket(printers.value)
    
    setupTempSocket(printers)

    console.log("PRINTERS: ", printers.value)

  } catch (error) {
    console.error('There has been a problem with your fetch operation:', error)
  }
})

onUnmounted(() => {
  // Clear the interval when the component is unmounted to prevent memory leaks
  if (intervalId) {
    clearInterval(intervalId)
  }
})

const sendToQueueView = (name: string | undefined) => {
  if (name) {
    router.push({ name: 'QueueViewVue', params: { printerName: name } });
  }
}

// set the status of the printer
const setPrinterStatus = async (printer: Device, status: string) => {
  await setStatus(printer.id, status); // update the status in the backend
  setTimeout(() => {
    // Using setTimeout to ensure the value is reset after the change event is processed
    const selectElement = document.querySelector('select');
    if (selectElement) {
      (selectElement as HTMLSelectElement).value = '';
    }
  });
}

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerToFind: Device, printerIdToPrintTo: number | undefined) => {
  await releaseJob(jobToFind, key, printerIdToPrintTo)
}

const setCurrent = (printer: Device, job: Job) => {
  currentPrinter.value = printer;
  currentJob.value = job;
  if (printer.name) {
    currentJob.value.printer = printer.name;
  }
}

const toTime = (seconds: number | undefined) => {
  if (seconds) {
    const date = new Date(seconds * 1000).toISOString().substr(11, 8);
    return date;
  }
  return "00:00:00";
}

const toDateString = (date: Date | undefined) => {
  if (date) {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    })
  }
  return '00:00 AM'
}
</script>

<template>
  <!-- bootstrap 'infoModal' -->
  <div class="modal fade" id="infoModal" tabindex="-1" aria-labelledby="infoModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="infoModalLabel"><b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <!-- Display other attributes of the job -->
          <div class="row">
            <div class="col-sm-12">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <h5 class="card-title"><i class="fas fa-chart-line"></i> <b>Progress:</b> {{ currentJob?.progress ?
            `${currentJob?.progress.toFixed(2)}%` : '0.00%' }}</h5>
                  <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                      :style="{ width: `${currentJob?.progress ? currentJob?.progress.toFixed(2) : '0'}%` }"
                      aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-hourglass-half"></i> <b>Elapsed Time:</b></h5>
                    </div>
                    <div class="col-12">{{ toTime(currentJob?.time?.elapsed) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-hourglass-end"></i> <b>Remaining Time:</b></h5>
                    </div>
                    <div class="col-12">{{ toTime(currentJob?.time?.remaining) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-stopwatch"></i> <b>Total Time:</b></h5>
                    </div>
                    <div class="col-12">
                      {{
            currentJob?.time?.extra && currentJob.time.extra > 0
              ? toTime(currentJob.time.total) + ' + ' + toTime(currentJob.time.extra)
              : toTime(currentJob?.time?.total)
          }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-stopwatch"></i> <b>ETA:</b></h5>
                    </div>
                    <div class="col-12">{{ (toDateString(currentJob?.time?.eta) ?? "00:00 AM") }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!--
              TIME
              (one test case)
              (printer was just booted up, i.e, printer was not heated up at all)

              job time on software: 00:38:53
                - timer starts when job is sent to printer
                - doesnt count for calibration time
                  - meaning timer increases when calibrating, making the print take longer than the time on the software
              time for print after softwares time finished: 00:02:49

              job time on printer: 00:40:03
                - timer starts when printer is heating up
            -->
          <div class="row">
            <div class="col-sm-12 col-md-6">
              <div class="card bg-light mb-3 h-100">
                <div class="card-body">
                  <h5 class="card-title"><i class="fas fa-file-alt"></i> <b>Job ID:</b> {{ currentJob?.id }}</h5>
                  <h5 class="card-title"><i class="fas fa-clock"></i> <b>Job Status:</b> {{ currentJob?.status }}</h5>
                  <h5 class="card-title"><i class="fas fa-file"></i> <b>File Name:</b> {{ currentJob?.file_name_original
                    }}</h5>
                </div>
              </div>
            </div>
            <div class="col-sm-12 col-md-6">
              <div class="card bg-light mb-3 h-100">
                <div class="card-body">
                  <h5 class="card-title">
                    <i class="fas fa-thermometer-full"></i>
                    <b>Nozzle Temp: </b>
                    <span
                      v-html="currentPrinter?.extruder_temp ? currentPrinter.extruder_temp + '&deg;C' : '<i>idle</i>'"></span>
                  </h5>
                  <h5 class="card-title">
                    <i class="fas fa-thermometer-half"></i>
                    <b>Bed Temp: </b>
                    <span
                      v-html="currentPrinter?.bed_temp ? currentPrinter.bed_temp + '&deg;C' : '<i>idle</i>'"></span>
                  </h5>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- bootstrap 'gcodeModal' -->
  <div class="modal fade" id="gcodeModal" tabindex="-1" aria-labelledby="gcodeModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeModalLabel"><b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class=" row">
            <div class="col-sm-12">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <h5 class="card-title">
                    <pre> .GCODE VIEWER </pre>
                  </h5>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>


  <div class="container">
    <b>Home</b>
    <table>
      <tr>
        <th>Job ID</th>
        <th>Printer name</th>
        <th>Printer Status</th>
        <th>Job Name</th>
        <th>File</th>
        <th>Progress</th>
        <th>Actions</th>
      </tr>
      <tr v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">
          here</RouterLink>, or restart the server.</tr>

      <tr v-for="printer in printers" :key="printer.id">
        <td
          v-if="(printer.status && (printer.status === 'printing' || printer.status === 'complete' || printer.status == 'paused')) && (printer.queue && printer.queue.length > 0 && printer.queue?.[0].status != 'inqueue')">
          {{ printer.queue?.[0].id }}
        </td>
        <td v-else><i>idle</i></td>
        <td><button type="button" class="btn btn-link" @click="sendToQueueView(printer.name)">{{ printer.name
            }}</button>
        </td>

        <td>
          <div class="d-flex align-items-center">
            <p class="mb-0 me-2">{{ printer.status }}</p>
            <div class="dropdown">
              <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton"
                data-bs-toggle="dropdown" aria-expanded="false">
                Change Status
              </button>
              <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                <li
                  v-if='printer.status == "configuring" || printer.status == "ready" || printer.status == "error" || printer.status == "complete"'>
                  <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'offline')">Turn Offline</a>
                </li>
                <li v-if='printer.status == "configuring" || printer.status == "offline" || printer.status == "error"'>
                  <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'ready')">Set to Ready</a>
                </li>
                <li v-if="printer.status == 'printing'"><a class="dropdown-item" href="#"
                    @click="setPrinterStatus(printer, 'complete')">Stop Print</a></li>
                <li v-if="printer.status == 'printing'"><a class="dropdown-item" href="#"
                    @click="setPrinterStatus(printer, 'paused')">Pause Print</a></li>
                <li v-if="printer.status == 'paused'"><a class="dropdown-item" href="#"
                    @click="setPrinterStatus(printer, 'printing')">Unpause Print</a></li>
              </ul>
            </div>
          </div>
        </td>

        <td
          v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
          {{ printer.queue?.[0]?.name }}
        </td>
        <td v-else></td>
        <td
          v-if="(printer.queue && printer.queue.length > 0 && (printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused') || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
          {{
            printer.queue?.[0]?.file_name_original }}</td>
        <td v-else></td>

        <!-- <div class="spinner-border" role="status">
          <span class="sr-only">Loading...</span>
        </div> -->

        <td style="width: 250px;">
          <div v-if="printer.status === 'printing' || printer.status == 'paused'">
            <!-- <div v-for="job in printer.queue" :key="job.id"> -->
            <!-- Display the elapsed time -->
            <div class="progress" style="position: relative;">
              <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"
                :aria-valuenow="printer.queue?.[0].progress" aria-valuemin="0" aria-valuemax="100">
              </div>
              <!-- job progress set to 2 decimal places -->
              <p style="position: absolute; width: 100%; text-align: center; color: black;">{{
            printer.queue?.[0].progress
              ?
              `${printer.queue?.[0].progress.toFixed(2)}%` : '0.00%' }}</p>
            </div>
            <!-- </div> -->
          </div>

          <div
            v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'complete' || printer.queue?.[0].status == 'cancelled')">
            <button type="button" class="btn btn-danger"
              @click="releasePrinter(printer.queue?.[0], 3, printer, printer.id)">Fail</button>
            <button type="button" class="btn btn-secondary"
              @click="releasePrinter(printer.queue?.[0], 1, printer, printer.id)">Clear</button>

            <!-- Clear/Rerun dropdown -->
            <div class="dropdown">
              <button class="btn btn-info dropdown-toggle" type="button" id="rerunDropdown" data-bs-toggle="dropdown"
                aria-expanded="false">
                Clear/Rerun
              </button>
              <ul class="dropdown-menu" aria-labelledby="rerunDropdown">
                <li v-for="rerunPrinter in printers" :key="rerunPrinter.id">
                  <a class="dropdown-item"
                    @click="releasePrinter(printer.queue?.[0], 2, rerunPrinter, rerunPrinter.id)">{{
            rerunPrinter.name
          }}</a>
                </li>
              </ul>
            </div>
          </div>
          <div
            v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'printing' && printer.status == 'complete')">
            <button class="btn btn-primary" type="button" disabled>
              <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <span class="sr-only">Finishing print...</span>
            </button>
          </div>
          <div v-else-if="printer.status == 'error'" class="alert alert-danger" role="alert">{{ printer?.error }}
          </div>
        </td>

        <td style="width: 1%; white-space: nowrap;">
          <div style="display: inline-flex;">
            <button type="button" class="btn btn-primary btn-circle me-2" data-bs-toggle="modal"
              data-bs-target="#infoModal" v-if="printer.queue && printer.queue.length > 0" v-bind:job="printer.queue[0]"
              @click="printer.name && setCurrent(printer, printer.queue[0])">
              <i class="fas fa-info"></i>
            </button>
            <button type="button" class="btn btn-success btn-circle" data-bs-toggle="modal" data-bs-target="#gcodeModal"
              v-if="printer.queue && printer.queue.length > 0" v-bind:job="printer.queue[0]"
              @click="printer.name && setCurrent(printer, printer.queue[0])">
              <i class="fas fa-code"></i>
            </button>
          </div>
        </td>
      </tr>
    </table>
  </div>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 2px solid #dddddd;
  /* Set border width and color */
  text-align: left;
  padding: 8px;
}

th {
  background-color: #f2f2f2;
}

p {
  margin: 0;
}

.btn-circle {
  width: 30px;
  height: 30px;
  padding: 0.375em 0;
  border-radius: 50%;
  font-size: 0.75em;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
</style>