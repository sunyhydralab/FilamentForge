<script setup lang="ts">
import { printers, type Device } from '../model/ports'
import { useGetJobs, type Job, useRerunJob, useDownloadFile } from '@/model/jobs';
import { computed, onMounted, ref } from 'vue';

const { jobhistory } = useGetJobs()
const { rerunJob } = useRerunJob()
const { getFile } = useDownloadFile()

const selectedPrinters = ref<Array<Device>>([])
let jobs = ref<Array<Job>>([])
let filter = ref('') // This will hold the current filter value
let oldestFirst = ref<boolean>(false)
let order = ref<string>('newest')

let page = ref(1)
let pageSize = ref(10)
let totalJobs = ref(0)
let totalPages = ref(1)

// computed property that returns the filtered list of jobs. 
let filteredJobs = computed(() => {
    if (filter.value) {
        return jobs.value.filter(job => job.printer.includes(filter.value))
    } else {
        return jobs.value
    }
})

onMounted(async () => {
    try {
        // job history now returns a tuple of joblist and total jobs, not just all the jobs in the database
        const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        // Calculate the total number of pages and store it in totalPages
        totalPages.value = Math.ceil(total / pageSize.value);
        // Ensure that totalPages is at least 1
        totalPages.value = Math.max(totalPages.value, 1);

    } catch (error) {
        console.error(error)
    }
})

const handleRerun = async (job: Job, printer: Device) => {
    try {
        await rerunJob(job, printer);
        console.log("JOBS FILE", job.file)
        // Fetch the updated list of jobs after rerunning the job
        // so when a job is rerun, the job history is updated
        const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)

        jobs.value = joblist;
        totalJobs.value = total;
    } catch (error) {
        console.error(error)
    }
}

// watch(pageSize, async (newPageSize) => {
//     jobs.value = []; // Clear the jobs array
//     // Fetch the updated list of jobs after changing the page size
//     const [joblist, total] = await jobhistory(page.value, newPageSize)
//     jobs.value = joblist;
//     totalJobs.value = total;
// })

const changePage = async (newPage: any) => {
    // Prevent the user from going to a page that doesn't exist
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    // Assign the new page value based on the parameter passed in
    page.value = newPage
    jobs.value = []; // Clear the jobs array
    // Fetch the updated list of jobs after changing the page
    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value)
    jobs.value = joblist;
    totalJobs.value = total;
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer)) {
        selectedPrinters.value.push(printer)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer)
    }
}

// watch(oldestFirst, async (newVal, oldVal) => {
//     if (newVal !== oldVal) {
//         // If the sorting order has changed, fetch the jobs for the current page again
//         const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
//         const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value)
//         jobs.value = joblist;
//         totalJobs.value = total;
//     }
// });

async function submitFilter() {
    jobs.value = []; // Clear the jobs array
    oldestFirst.value = order.value === 'oldest';
    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];

    // Get the total number of jobs first, without considering the page number
    const [, total] = await jobhistory(1, Number.MAX_SAFE_INTEGER, printerIds, oldestFirst.value);
    totalJobs.value = total;

    // Calculate the total number of pages and store it in totalPages
    totalPages.value = Math.ceil(totalJobs.value / pageSize.value);

    // Ensure that totalPages is at least 1
    totalPages.value = Math.max(totalPages.value, 1);

    // If the current page is greater than the total number of pages, set the current page to the last page
    if (page.value > totalPages.value) {
        page.value = totalPages.value;
    }

    // Now fetch the jobs for the current page
    const [joblist] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value);
    jobs.value = joblist;
}
</script>

<template>
    <div class="container">
        <h2 class="mb-2 text-center">Job History View</h2>
        <div class="mb-2 p-2 border rounded">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <label for="pageSize" class="form-label">Jobs per page:</label>
                    <input id="pageSize" type="number" v-model.number="pageSize" min="1" class="form-control">
                </div>

                <div class="col-md-4">
                    <label class="form-label">Device:</label>
                    <div class="dropdown w-100">
                        <button class="btn btn-secondary dropdown-toggle w-100" type="button" id="dropdownMenuButton"
                            data-bs-toggle="dropdown" aria-expanded="false">
                            Select Printer
                        </button>
                        <ul class="dropdown-menu w-100" aria-labelledby="dropdownMenuButton">
                            <li v-for="printer in printers" :key="printer.id">
                                <div class="form-check" @click.stop>
                                    <input class="form-check-input" type="checkbox" :value="printer"
                                        @change="appendPrinter(printer)" :id="'printer-' + printer.id">
                                    <label class="form-check-label" :for="'printer-' + printer.id">
                                        {{ printer.name }}
                                    </label>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col-md-4">
                    <label class="form-label">Order:</label>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="order" id="orderNewest" value="newest"
                            v-model="order">
                        <label class="form-check-label" for="orderNewest">
                            Newest to Oldest
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="order" id="orderOldest" value="oldest"
                            v-model="order">
                        <label class="form-check-label" for="orderOldest">
                            Oldest to Newest
                        </label>
                    </div>
                </div>
            </div>
        </div>

        <div class="mb-2">
            <button @click="submitFilter" class="btn btn-primary">Submit Filter</button>
        </div>
        <table class="table">
            <thead>
                <tr>
                    <th class="col-job-id">Job ID</th>
                    <th class="col-job-title">Job Title</th>
                    <th class="col-file">File</th>
                    <th class="col-date">Date Completed</th>
                    <th class="col-status">Final Status</th>
                    <th class="col-printer">Printer</th>
                    <th class="col-rerun">Rerun Job</th>
                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.id">
                    <td>{{ job.id }}</td>
                    <td>{{ job.name }}</td>
                    <td>
                        {{ job.file_name_original }}
                        <button class="btn btn-secondary download" @click="getFile(job.id)">
                            <i class="fas fa-download"></i>
                        </button>
                    </td>
                    <td>{{ job.date }}</td>
                    <td>{{ job.status }}</td>
                    <td>{{ job.printer }}</td>
                    <td>
                        <div class="dropdown">
                            <button class="btn btn-secondary dropdown-toggle" type="button" id="printerDropdown"
                                data-bs-toggle="dropdown" aria-expanded="false">
                                Rerun Job
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="printerDropdown">
                                <li v-for="printer in printers" :key="printer.id">
                                    <a class="dropdown-item" @click="handleRerun(job, printer)">{{ printer.name }}</a>
                                </li>
                            </ul>
                        </div>
                    </td>
                </tr>

            </tbody>

            <tbody v-else>
                <tr>
                    <td colspan="7">No jobs found. Submit your first job <RouterLink to="/submit">here!</RouterLink>
                    </td>
                </tr>
            </tbody>
        </table>
        <p class="mt-2">Total Jobs: {{ totalJobs }}</p>
        <nav aria-label="Page navigation">
            <ul class="pagination">
                <li class="page-item" :class="{ 'disabled': page <= 1 }">
                    <a class="page-link" href="#" @click.prevent="changePage(page - 1)">Previous</a>
                </li>
                <li class="page-item disabled"><a class="page-link">Page {{ page }} of {{ totalPages }}</a></li>
                <li class="page-item" :class="{ 'disabled': page >= totalPages }">
                    <a class="page-link" href="#" @click.prevent="changePage(page + 1)">Next</a>
                </li>
            </ul>
        </nav>
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

.col-job-id {
    width: 8vh;
}

.col-job-title {
    width: 20vh;
}

.col-file {
    width: 35vh;
}

.col-date {
    width: 26vh;
    overflow-x: auto;
    /* Add a horizontal scrollbar if necessary */
    white-space: nowrap;
    /* Prevent the content from wrapping to the next line */
}

.col-status {
    width: 12vh;
}

.col-printer {
    width: 20vh;
}

.col-rerun {
    width: 5vh;
}

ul.dropdown-menu.w-100.show li {
    margin-left: 1rem;
}

.form-check-input:focus,
.form-control:focus {
    outline: none;
    box-shadow: none;
    border-color: #dee2e6;
}

label.form-check-label {
    cursor: pointer;
}

.download {
    float: right;
}
</style>