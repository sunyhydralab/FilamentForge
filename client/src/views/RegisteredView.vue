<script setup lang="ts">
import { useGetPorts, useRegisterPrinter, useRetrievePrinters, useHardReset, useQueueRestore, useDeletePrinter, useNullifyJobs, useEditName, useRemoveThread, useEditThread, useDiagnosePrinter, type Device } from '../model/ports'
import { ref, onMounted } from 'vue';
const { ports } = useGetPorts();
const { register } = useRegisterPrinter();
const { retrieve } = useRetrievePrinters();
const { hardReset } = useHardReset();
const { queueRestore } = useQueueRestore();
const { deletePrinter } = useDeletePrinter();
const { nullifyJobs } = useNullifyJobs();
const { editName } = useEditName();
const { removeThread } = useRemoveThread();
const { editThread } = useEditThread();
const { diagnose } = useDiagnosePrinter();

let devices = ref<Array<Device>>([]); // Array of all devices -- stores ports for user to select/register
let selectedDevice = ref<Device | null>(null) // device user selects to register.
let customname = ref('') // Stores the user input name of printer 
let registered = ref<Array<Device>>([]) // Stores array of printers already registered in the system
let editMode = ref(false)
let editNum = ref<number | undefined>(0)
let newName = ref('')
let message = ref('')
let showMessage = ref(false)
let messageId = ref<number | undefined>(0)

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    try {
        const allDevices = await ports();  // load all ports
        registered.value = await retrieve();  // loads registered printers into registered array

        devices.value = allDevices

    } catch (error) {
        console.error(error);
    }
});

const doRegister = async () => {
    if (selectedDevice.value && customname.value) {
        selectedDevice.value = {
            device: selectedDevice.value.device,
            description: selectedDevice.value.description,
            hwid: selectedDevice.value.hwid,
            name: customname.value.trim(), // Trim to remove leading and trailing spaces
        };

        await register(selectedDevice.value);

        // Fetch the updated list after registration
        registered.value = await retrieve();

        // Refresh the devices list
        const allDevices = await ports();
        devices.value = allDevices.filter((device: Device) =>
            !registered.value.some(registeredDevice => registeredDevice.device === device.device)
        );
    }

    // reset values 
    selectedDevice.value = null;
    customname.value = ''
}

const doHardReset = async (printer: Device) => {
    await hardReset(printer.id)
}

const doQueueRestore = async (printer: Device) => {
    await queueRestore(printer.id)
}

const doDelete = async (printer: Device) => {
    registered.value = registered.value.filter(p => p.id !== printer.id)
    await removeThread(printer.id)
    await nullifyJobs(printer.id)
    await deletePrinter(printer.id)
}

const saveName = async (printer: Device) => {
    await editThread(printer.id, newName.value.trim())
    await editName(printer.id, newName.value.trim())
    printer.name = newName.value.trim();

    editMode.value = false
    newName.value = ''
    editNum.value = undefined // reset editNum
}

const doDiagnose = async (printer: Device) => {
    message.value = `Diagnosing ${printer.name}:<br/><br/>This printer is registered under port ${printer.device}.`
    showMessage.value = true
    let str = await diagnose(printer.device)
    let resstr = str.diagnoseString
    message.value += "<br><br>" + resstr
}

const clearMessage = () => {
    showMessage.value = false
    messageId.value = 0
    message.value = ''
}

</script>
<template>
    <div class="container">
        <b>Registered View</b>

        <div v-if="registered.length != 0">
            <div class="card" style="width: 18rem;" v-for="printer in registered">
                <div class="card-body">
                    <button @click="doHardReset(printer)">Hard Reset</button>
                    <button @click="doQueueRestore(printer)">Restore Queue</button>
                    <button @click="doDelete(printer)">Deregister</button>

                    <h6 v-if="!editMode || !(editNum == printer.id)"
                        @click="editMode = true; editNum = printer.id; newName = printer.name || ''" style="cursor: pointer;">
                        Name: {{ printer.name }} (Click
                        to edit)</h6>
                    <div v-else>
                        <input type="text" v-model="newName">
                        <button @click="saveName(printer)">Save</button>
                        <button @click="editMode = false; editNum = undefined; newName = ''">Cancel</button>
                    </div>


                    <h6 class="card-subtitle mb-2 text-body-secondary">{{ printer.device }}</h6>
                    <h6>Description: {{ printer.description }}</h6>
                    <h6>hwid: {{ printer.hwid }}</h6>
                    <h6>Date registered: {{ printer.date }}</h6>

                    <button @click="messageId = printer.id; doDiagnose(printer)">Diagnose Printer</button>
                    <br><br>
                    <div v-if="messageId == printer.id && showMessage == true" style="color:red;">
                        <b v-html="message"></b>
                        <button @click="clearMessage">Clear message</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="form-container">
            <b class="register">REGISTER PRINTERS</b>
            <form methods="POST" @submit="doRegister">
                <select name="ports" id="ports" v-model="selectedDevice" required>
                    <option disabled value="null">Select Device</option> <!-- Default option -->
                    <option v-for="printer in devices" :value="printer">
                        {{ printer.device }}
                    </option>
                </select>
                <br><br>
                <div v-if="selectedDevice">
                    <b>Device: </b>
                    {{ selectedDevice.device }}
                    <br>
                    <b>Description: </b>
                    {{ selectedDevice.description }}
                    <br>
                    <b>hwid: </b>
                    {{ selectedDevice.hwid }}
                </div>
                <div v-else>
                    No Device Selected
                </div>
                <div v-if="selectedDevice">
                    <label for="name"></label>
                    <input type="text" placeholder="Custom Name" maxlength="49" v-model="customname" required>
                    <br><br>
                    <input type="submit" value="Submit">
                </div>
            </form>
        </div>
    </div>
</template>

<style>
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

.register {
    color: red;
}
</style>