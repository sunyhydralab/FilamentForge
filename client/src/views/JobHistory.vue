<script setup lang="ts">
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useGetJobs, type Job, useRerunJob, useGetJobFile, useDeleteJob, useClearSpace, useFavoriteJob } from '../model/jobs';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const { jobhistory, getFavoriteJobs } = useGetJobs()
const { retrieveInfo } = useRetrievePrintersInfo()
const { rerunJob } = useRerunJob()
const { getFile } = useGetJobFile()
const { deleteJob } = useDeleteJob()
const { clearSpace } = useClearSpace()
const { favorite } = useFavoriteJob()

const printers = ref<Array<Device>>([]) // Get list of open printer threads 
const selectedPrinters = ref<Array<Number>>([])
const selectedJobs = ref<Array<Job>>([]);
const deleteModalTitle = computed(() => `Deleting ${selectedJobs.value.length} job(s) from database!`);
const searchJob = ref(''); // This will hold the current search query
const searchByJobName = ref(true);
const searchByFileName = ref(true);

const router = useRouter();

let jobs = ref<Array<Job>>([])
let filter = ref('')
let oldestFirst = ref<boolean>(false)
let order = ref<string>('newest')

let page = ref(1)
let pageSize = ref(10)
let totalJobs = ref(0)
let totalPages = ref(1)
let selectAllCheckbox = ref(false);

let modalTitle = ref('');
let modalMessage = ref('');
let modalAction = ref('');
let searchCriteria = ref('');

let buttonTransform = ref(0);
let favoriteJobs = ref<Array<Job>>([])
let jobToUnfavorite: Job | null = null;

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
        const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        totalPages.value = Math.ceil(total / pageSize.value);
        totalPages.value = Math.max(totalPages.value, 1);

        const printerInfo = await retrieveInfo()
        printers.value = printerInfo

        favoriteJobs.value = await getFavoriteJobs()
    } catch (error) {
        console.error(error)
    }
})

const handleRerun = async (job: Job, printer: Device) => {
    await router.push({
        name: 'SubmitJobVue', // the name of the route to SubmitJob.vue
        params: { job: JSON.stringify(job), printer: JSON.stringify(printer) } // the job and printer to fill in the form
    });
}

const changePage = async (newPage: any) => {
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    selectedJobs.value = [];
    selectAllCheckbox.value = false;

    page.value = newPage
    jobs.value = []; // Clear the jobs array
    // Fetch the updated list of jobs after changing the page
    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value)
    jobs.value = joblist;
    totalJobs.value = total;
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer.id!)) {
        selectedPrinters.value.push(printer.id!)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer.id)
    }
}

async function submitFilter() {
    jobs.value = []
    oldestFirst.value = order.value === 'oldest';
    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];

    if (searchByJobName.value && !searchByFileName.value) {
        searchCriteria.value = 'searchByJobName';
    } else if (!searchByJobName.value && searchByFileName.value) {
        searchCriteria.value = 'searchByFileName';
    } else {
        searchCriteria.value = searchJob.value;
    }

    // Get the total number of jobs first, without considering the page number
    const [, total] = await jobhistory(1, Number.MAX_SAFE_INTEGER, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value);
    totalJobs.value = total;

    totalPages.value = Math.ceil(totalJobs.value / pageSize.value);
    totalPages.value = Math.max(totalPages.value, 1);

    if (page.value > totalPages.value) {
        page.value = totalPages.value;
    }

    // Now fetch the jobs for the current page
    const [joblist] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value);
    jobs.value = joblist;

    selectedJobs.value = [];
    selectAllCheckbox.value = false;
}

function clearFilter() {
    searchJob.value = '';
    selectedPrinters.value = [];

    const checkboxesToClear = document.querySelectorAll<HTMLInputElement>('.form-check-input.clearable-checkbox');
    checkboxesToClear.forEach(checkbox => {
        checkbox.checked = false;
    });

    if (order.value === 'oldest') {
        order.value = 'newest';
    }

    submitFilter();
}

const ensureOneCheckboxChecked = () => {
    if (!searchByJobName.value && !searchByFileName.value) {
        searchByJobName.value = true;
    }
}

// This just displays the selectedJobs on the console for me to see while working. Would be removed before final merge
const handleJobSelection = () => {
    console.log('Selected Jobs:', selectedJobs.value);
};

const confirmDelete = async () => {
    const deletionPromises = selectedJobs.value.map(job => deleteJob(job));
    await Promise.all(deletionPromises);

    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];
    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value);
    jobs.value = joblist;
    totalJobs.value = total;

    submitFilter();

    // Clear the selected jobs array
    selectedJobs.value = [];
    selectAllCheckbox.value = false;

    submitFilter();

    favoriteJobs.value = await getFavoriteJobs();
}

const selectAllJobs = () => {
    if (selectAllCheckbox.value) {
        const newSelectedJobs = filteredJobs.value.filter(job => !selectedJobs.value.includes(job));
        selectedJobs.value = [...selectedJobs.value, ...newSelectedJobs];
    } else {
        selectedJobs.value = selectedJobs.value.filter(job => !filteredJobs.value.includes(job));
    }
}

async function clear() {
    await clearSpace()
    // might need a fix here
    submitFilter()
}

const openModal = (title: any, message: any, action: any) => {
    modalTitle.value = title;
    modalMessage.value = message;
    modalAction.value = action;
}

const favoriteJob = async (job: Job, fav: boolean) => {
    await favorite(job, fav);
    favoriteJobs.value = await getFavoriteJobs();

    jobs.value = jobs.value.map(j => {
        if (j.id === job.id) {
            j.favorite = fav;
        }
        return j;
    })

    jobToUnfavorite = null;
}

const toggleButton = () => {
    buttonTransform.value = buttonTransform.value === 0 ? -700 : 0;
}

</script>

<template>
    <!-- bootstrap off canvas to the right -->
    <div class="offcanvas offcanvas-end" data-bs-backdrop="static" tabindex="-1" id="offcanvasRight"
        aria-labelledby="offcanvasRightLabel">
        <div class="offcanvas-header bg-primary text-white">
            <div class="container-fluid">
                <div class="row align-items-center">
                    <div class="col">
                        <h5 class="offcanvas-title" id="offcanvasRightLabel">Favorite Prints</h5>
                    </div>
                    <div class="col-auto">
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"
                            aria-label="Close" v-on:click="toggleButton"></button>
                    </div>
                </div>
            </div>
        </div>
        <div class="offcanvas-body" style="max-height: 100vh; overflow-y: auto;">
            <div class="grid-container header">
                <h5>Job Name</h5>
                <h5>File Name</h5>
                <h5>Actions</h5>
            </div>
            <div v-if="favoriteJobs.length > 0" v-for="job in favoriteJobs" :key="job.id" class="mb-3">
                <div class="grid-container job">
                    <p class="my-auto">{{ job.name }}</p>
                    <p class="my-auto">{{ job.file_name_original }}</p>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-star text-warning" style="margin-right: 10px;" data-bs-toggle="modal" data-bs-target="#favoriteModal"
                            @click="jobToUnfavorite = job"></i>
                        <button class="btn btn-secondary download" style="margin-right: 10px;" @click="getFile(job.id)"
                            :disabled="job.file_name_original.includes('.gcode:')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-secondary dropdown-toggle" type="button" id="printerDropdown"
                            data-bs-toggle="dropdown" aria-expanded="false"
                            :disabled="job.file_name_original.includes('.gcode:')">
                            <i class="fa-solid fa-arrow-rotate-right"></i>
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="printerDropdown">
                            <li v-for="printer in printers" :key="printer.id">
                                <a class="dropdown-item" @click="handleRerun(job, printer)" data-bs-dismiss="offcanvas">{{ printer.name }}</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <p v-else class="text-center text-muted">No favorite jobs found. Favorite your first job!</p>
        </div>
    </div>
    <div class="offcanvas-btn-box" :style="{ transform: `translateX(${buttonTransform}px)` }">
        <button class="btn btn-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasRight"
            aria-controls="offcanvasRight" v-on:click="toggleButton"
            style="border-top-right-radius: 0; border-bottom-right-radius: 0; padding: 5px 10px;">
            <span><i class="fas fa-chevron-left"></i></span>
            <span><i class="fas fa-star"></i></span>
        </button>
    </div>

    <!-- modal to unfavorite a job in the off canvas -->
    <div class="modal fade" id="favoriteModal" tabindex="-1" aria-labelledby="favoriteModalLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="favoriteModalLabel">Unfavorite Job</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to unfavorite this job?</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal"
                        @click="favoriteJob(jobToUnfavorite!, false)">Unfavorite</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">

        <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true"
            data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="exampleModalLabel">{{ modalTitle }}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p v-html="modalMessage"></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button v-if="modalAction === 'confirmDelete'" type="button" class="btn btn-danger"
                            data-bs-dismiss="modal" @click="confirmDelete">Delete</button>
                        <button v-if="modalAction === 'clear'" type="button" class="btn btn-danger"
                            data-bs-dismiss="modal" @click="clear">Clear Space</button>
                    </div>
                </div>
            </div>
        </div>

        <h2 class="mb-2 text-center">Job History View</h2>
        <div class="container-fluid mb-2 p-2 border rounded">
            <div class="row justify-content-center">

                <div class="col d-flex align-items-center justify-content-between">
                    <label for="pageSize" class="form-label my-auto" style="white-space: nowrap;">Jobs per page:</label>
                    <input id="pageSize" type="number" v-model.number="pageSize" min="1"
                        class="form-control mx-2 my-auto">
                    <label class="my-auto">/&nbsp;{{ totalJobs }}</label>
                </div>

                <div class="col d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center">
                        <label class="form-label">Device:</label>
                        <div style="width: 10px;"></div> <!-- This div will create a white space -->
                    </div>
                    <div class="dropdown w-100">
                        <button class="btn btn-secondary dropdown-toggle w-100" type="button" id="dropdownMenuButton"
                            data-bs-toggle="dropdown" aria-expanded="false">
                            Select Printer
                        </button>
                        <ul class="dropdown-menu w-100" aria-labelledby="dropdownMenuButton">
                            <li v-for="printer in printers" :key="printer.id">
                                <div class="form-check" @click.stop>
                                    <input class="form-check-input clearable-checkbox" type="checkbox" :value="printer"
                                        @change="appendPrinter(printer)" :id="'printer-' + printer.id">
                                    <label class="form-check-label" :for="'printer-' + printer.id">
                                        {{ printer.name }}
                                    </label>
                                </div>
                            </li>
                            <li class="dropdown-divider"></li>
                            <li>
                                <div class="form-check" @click.stop>
                                <input class="form-check-input clearable-checkbox" type="checkbox" id="deregistered-printers"
                                    @click="selectedPrinters.push(0)">
                                <label class="form-check-label" for="deregistered-printers">
                                    Deregistered printers
                                </label>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col d-flex align-items-center">
                    <label class="form-label d-flex align-items-center">Order:</label>
                    <div style="padding-left: 1rem;">
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
                <div class="col-md-4">
                    <input type="text" v-model="searchJob" placeholder="Search for jobs" class="form-control">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="searchByJobName" v-model="searchByJobName" @change="ensureOneCheckboxChecked">
                        <label class="form-check-label" for="searchByJobName">
                            Search by Job Name
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="searchByFileName" v-model="searchByFileName" @change="ensureOneCheckboxChecked">
                        <label class="form-check-label" for="searchByFileName">
                            Search by File Name
                        </label>
                    </div>
                </div>

                <div class="col d-flex align-items-center justify-content-between">
                    <button @click="clear" class="btn btn-danger w-100">Clear Space</button>
                </div>

            </div>
        </div>
        <div class="row w-100" style="margin-bottom: 0.5rem;">
            <div class="col-1 text-start" style="padding-left: 0">
                <button type="button"
                    @click="openModal(deleteModalTitle, 'Are you sure you want to delete these jobs? This action cannot be <b>undone</b>.', 'confirmDelete')"
                    class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#exampleModal"
                    :disabled="selectedJobs.length === 0">
                    <i class="fas fa-trash-alt"></i>
                </button>

            </div>
            <div class="col-10 text-center">
                <button @click="submitFilter" class="btn btn-primary">Submit Filter</button>
                &nbsp; &nbsp;
                <button @click="clearFilter" class="btn btn-danger">Clear Filter</button>
            </div>
            <div class="col-1">
                <!-- Empty column to push the other columns to the left -->
                <!-- maybe put clear space here?? would be above the rerun job column -->
            </div>
        </div>

        <table class="table">
            <thead>
                <tr>
                    <th class="col-checkbox">
                        <input type="checkbox" @change="selectAllJobs" v-model="selectAllCheckbox">
                    </th>
                    <th>Job ID</th>
                    <th>Job Title</th>
                    <th>File</th>
                    <th>Date Completed</th>
                    <th>Final Status</th>
                    <th>Printer</th>
                    <th>Rerun Job</th>
                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.id">
                    <td>
                        <input type="checkbox" v-model="selectedJobs" :value="job">
                    </td>
                    <td>{{ job.id }}</td>
                    <td>
                        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                            <div>{{ job.name }}</div>
                            <div class="star-icon">
                                <i v-if="job.favorite === true" class="fas fa-star text-warning"
                                    @click="favoriteJob(job, false)"></i>
                                <i v-else class="far fa-star text-warning" @click="favoriteJob(job, true)"></i>
                            </div>
                        </div>
                    </td>
                    <td>
                        {{ job.file_name_original }}
                        <button class="btn btn-secondary download" @click="getFile(job.id)"
                            :disabled="job.file_name_original.includes('.gcode:')">
                            <i class="fas fa-download"></i>
                        </button>
                    </td>
                    <td>{{ job.date }}</td>
                    <td>{{ job.status }}</td>
                    <td>{{ job.printer }}</td>
                    <td>
                        <div class="dropdown">
                            <button class="btn btn-secondary dropdown-toggle" type="button" id="printerDropdown"
                                data-bs-toggle="dropdown" aria-expanded="false"
                                :disabled="job.file_name_original.includes('.gcode:')">
                                <i class="fa-solid fa-arrow-rotate-right"></i>
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
                    <td colspan="8">No jobs found. Submit your first job <RouterLink to="/submit">here!</RouterLink>
                    </td>
                </tr>
            </tbody>
        </table>
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
.grid-container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 10px;
}

.header {
    border: 1px solid #e0e0e0;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
    background-color: #f2f2f2;
}

.header h5 {
    text-decoration: underline;
}

.job {
    border: 1px solid #e0e0e0;
    padding: 10px;
    border-radius: 5px;
}

.offcanvas {
    width: 700px;
}

.offcanvas-btn-box {
    transition: transform .3s ease-in-out;
    position: fixed;
    top: 50%;
    right: 0;
    z-index: 1041;
}

.offcanvas-end {
    border-left: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    border: 2px solid #dddddd;
    text-align: left;
    padding: 8px;
}

th {
    background-color: #f2f2f2;
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