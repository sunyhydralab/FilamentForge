<script setup lang="ts">
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useAddJobToQueue, type Job } from '../model/jobs'
import { ref, onMounted } from 'vue'

const { retrieveInfo } = useRetrievePrintersInfo()
const { addJobToQueue } = useAddJobToQueue()
const printers = ref<Array<Device>>([])

// Collect form data
const selectedPrinter = ref<Device | null>(null)
const file = ref<File>()
const quantity = ref<number>(1)
const priority = ref<boolean>(false)
const name = ref<string>()

// file upload
const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement
    file.value = target.files ? target.files[0] : undefined
}

// fills printers array with printers that have threads from the database
onMounted(async () => {
    try {
        printers.value = await retrieveInfo()
    } catch (error) {
        console.error('There has been a problem with your fetch operation:', error)
    }
})

// sends job to printer queue
const handleSubmit = async () => {
    if (selectedPrinter.value) {
        for (let i = 0; i < quantity.value; i++) {
            const job: Job = {
                //name of file
                name: name.value as string,
                file: file.value as File,
                // date: new Date(),
                // status: selectedPrinter.value?.status as string,
                printerid: selectedPrinter.value?.id as number,
            }
            // send job to printers queue
            try {
                await addJobToQueue(job)
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error)
            }
        }
    }    
}

</script>
<template>
    <div class="container">
        <p>Submit Job View</p>

        <div class="form-container">
            <form @submit.prevent="handleSubmit">
                <select v-model="selectedPrinter" required>
                    <option value="None">Device: None</option>
                    <option v-for="printer in printers" :value="printer" :key="printer.id">
                        {{ printer.name }}
                        <!-- maybe show the status of the printer here??? -->
                    </option>
                </select>
                <br><br>
                Upload your .gcode file
                <!-- Decide which file types are compatible with which printer. .gcode v-if printer is compatible with .gcode, .x3g if with .x3g, etc -->
                <input @change="handleFileUpload" type="file" id="file" name="file" accept=".gcode" required>
                <br><br>

                <!-- Make it so user can't insert negative quantity. Decide on upper limit. -->
                <!-- Make load-balancing feature -->
                <label for="name">Quantity</label>
                <input v-model="quantity" type="number" id="quantity" name="quantity" min="0" required>
                <br><br>

                <label for="priority">Priority job?</label>
                <input v-model="priority" type="checkbox" id="priority" name="priority">
                <br><br>

                <label for="name">Name</label>
                <input v-model="name" type="text" id="name" name="name">

                <br><br>
                <!-- This form data does NOT go into the database -- goes into in-memory printer array to be handled. 
                    Also is sent to the QueueView. Perhaps the form is sent to the backend and queueview retrieves that data
                    from the backend. 
                    The job data only gets inserted into the Job table once it is done printing. 
                -->
                <input type="submit" value="Submit">
            </form>
        </div>
    </div>
</template>

<style scoped>
.container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.form-container {
    border: 2px solid #333;
    padding: 20px;
    margin-top: 20px;
    width: 300px;
}
</style>