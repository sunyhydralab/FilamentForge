<script setup lang="ts">
import { printers, type Device } from '../model/ports'
import { useAddJobToQueue, useAutoQueue } from '../model/jobs'
import { ref, onMounted } from 'vue'
import { toast } from '@/model/toast';

const { addJobToQueue } = useAddJobToQueue()
const { auto } = useAutoQueue()

// Form reference
const form = ref<HTMLFormElement | null>(null);

// Collect form data
// const selectedPrinter = ref<Device | null>(null)

const selectedPrinters = ref<Array<Device>>([])


const file = ref<File>()
const quantity = ref<number>(1)
const priority = ref<number>(0)
const name = ref<string>()

const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const uploadedFile = target.files ? target.files[0] : undefined;
    if (uploadedFile && uploadedFile.name.length > 50) {
        toast.error('The file name should not be longer than 50 characters');
        target.value = ''
    } else {
        file.value = uploadedFile;
    }
}

// validate quantity
const validateQuantity = () => {
    if (quantity.value < 1) {
        quantity.value = 1
    }
    if (quantity.value < selectedPrinters.value.length) {
        toast.error('Quantity must be greater than or equal to the number of selected printers')
        return false;
    }
    return true;
}

const onlyNumber = ($event: KeyboardEvent) => {
    let keyCode = $event.keyCode;
    if ((keyCode < 48 || keyCode > 57) && keyCode !== 8) { // 48-57 are the keycodes for 0-9, 8 is for backspace
        $event.preventDefault();
    }
}

// sends job to printer queue
const handleSubmit = async () => {
    if (selectedPrinters.value.length == 0) {
        let numPrints = quantity.value
        for (let i = 0; i < numPrints; i++) {
            const formData = new FormData() // create FormData object
            formData.append('file', file.value as File) // append form data
            formData.append('name', name.value as string)
            formData.append('priority', priority.value.toString())
            try {
                await auto(formData)
                if (form.value) {
                    form.value.reset()
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error)
            }
        }
        resetValues()
    }

    let sub = validateQuantity()
    let res = null
    if (sub == true) {
        if (selectedPrinters.value.length == 0) {
            let numPrints = quantity.value
            for (let i = 0; i < numPrints; i++) {
                const formData = new FormData() // create FormData object
                formData.append('file', file.value as File) // append form data
                formData.append('name', name.value as string)
                formData.append('priority', priority.value.toString())
                try {
                    res = await auto(formData)
                    if (form.value) {
                        form.value.reset()
                    }
                } catch (error) {
                    console.error('There has been a problem with your fetch operation:', error)
                }
            }
            resetValues()
        }
        else {
            let printsPerPrinter = Math.floor(quantity.value / selectedPrinters.value.length) // number of even prints per printer
            let remainder = quantity.value % selectedPrinters.value.length; //remainder to be evenly distributed 
            for (const printer of selectedPrinters.value) {
                let numPrints = printsPerPrinter
                if (remainder > 0) {
                    numPrints += 1
                    remainder -= 1
                }
                for (let i = 0; i < numPrints; i++) {
                    const formData = new FormData() // create FormData object
                    formData.append('file', file.value as File) // append form data
                    formData.append('name', name.value as string)
                    formData.append('printerid', printer?.id?.toString() || '');
                    formData.append('priority', priority.value.toString())
                    try {
                        res = await addJobToQueue(formData)
                        // reset form
                        if (form.value) {
                            form.value.reset()
                        }
                        // reset Vue refs
                    } catch (error) {
                        console.error('There has been a problem with your fetch operation:', error)
                    }
                }
            }
            resetValues()
        }
    }
    if (res.success == true) {
        toast.success('Job added to queue')
    } else {
        toast.error('Job failed to add to queue')
    }
}

function resetValues() {
    selectedPrinters.value = [];
    quantity.value = 1;
    priority.value = 0;
    name.value = undefined;
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer)) {
        selectedPrinters.value.push(printer)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer)
    }
}

</script>
<template>
    <div class="container py-5">
        <h2 class="mb-4">Submit Job View</h2>

        <div class="card">
            <div class="card-body">
                <form @submit.prevent="handleSubmit" ref="form">

                    <div class="mb-3">
                        <label for="printer" class="form-label">Select Printer</label>
                        <select id="printer" class="form-select" required multiple>
                            <option :value="null">Auto Queue</option>
                            <option v-for="printer in printers" :value="printer" :key="printer.id"
                                @click="appendPrinter(printer)">
                                {{ printer.name }}
                            </option>
                        </select>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Selected printer(s):</label>
                        <p v-for="printer in selectedPrinters" class="mb-1">
                            <b>{{ printer.name }}</b> status: {{ printer.status }}
                        </p>
                    </div>

                    <div class="mb-3">
                        <label for="file" class="form-label">Upload your .gcode file</label>
                        <input @change="handleFileUpload" class="form-control" type="file" id="file" name="file" accept=".gcode" required>
                    </div>

                    <div class="mb-3">
                        <label for="quantity" class="form-label">Quantity</label>
                        <input v-model="quantity" class="form-control" type="number" id="quantity" name="quantity" min="1" required
                               @keydown="onlyNumber($event)">
                    </div>
                    <div class="mb-3 form-check">
                        <input v-model="priority" class="form-check-input" type="checkbox" id="priority" name="priority">
                        <label class="form-check-label" for="priority">Priority job?</label>
                    </div>

                    <div class="mb-3">
                        <label for="name" class="form-label">Name</label>
                        <input v-model="name" class="form-control" type="text" id="name" name="name" required>
                    </div>

                    <div class="mb-3">
                        <input class="btn btn-primary" type="submit" value="Add to queue(s)">
                    </div>
                </form>
            </div>
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