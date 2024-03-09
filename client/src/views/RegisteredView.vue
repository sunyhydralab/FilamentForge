<script setup lang="ts">
import { useGetPorts, useRegisterPrinter, useRetrievePrinters, useHardReset, useQueueRestore, type Device } from '../model/ports'
import { ref, onMounted } from 'vue';
const { ports } = useGetPorts();
const { register } = useRegisterPrinter();
const { retrieve } = useRetrievePrinters();
const { hardReset } = useHardReset();
const { queueRestore } = useQueueRestore(); 

let devices = ref<Array<Device>>([]); // Array of all devices -- stores ports for user to select/register
let selectedDevice = ref<Device | null>(null) // device user selects to register.
let customname = ref('') // Stores the user input name of printer 
let registered = ref<Array<Device>>([]) // Stores array of printers already registered in the system

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    try {
        const allDevices = await ports();  // load all ports
        registered.value = await retrieve();  // loads registered printers into registered array

        devices.value = allDevices

        // Filter out the already registered devices
        // devices.value = allDevices.filter((device: Device) =>
        //     !registered.value.some(registeredDevice => registeredDevice.device === device.device)
        // );
        // console.log(registered.value);

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

</script>
<template>
    <div class="container">
        <b>Registered View</b>

        <div v-if="registered.length != 0">
            <div class="card" style="width: 18rem;" v-for="printer in registered">
                <div class="card-body">
                    <button class="btn btn-danger me-2" @click="doHardReset(printer)">Hard Reset</button>
                    <button class="btn btn-warning" @click="doQueueRestore(printer)">Restore Queue</button>
                    <h6><strong>Name:</strong> {{ printer.name }}</h6>
                    <h6 class="card-subtitle mb-2 text-body-secondary"><strong>Device:</strong> {{ printer.device }}</h6>
                    <h6><strong>Description:</strong> {{ printer.description }}</h6>
                    <h6><strong>hwid:</strong> {{ printer.hwid }}</h6>
                    <h6><strong>Date registered:</strong> {{ printer.date }}</h6>
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