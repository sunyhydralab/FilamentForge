<script setup lang="ts">
import { onMounted, toRef, watchEffect, ref, nextTick, computed } from 'vue'
import type { Job } from '@/model/jobs';

const props = defineProps({
    job: Object as () => Job | null
})
const job = toRef(props, 'job')

let isPaused = ref(false)
let lastVisibleLineIndex = ref(0)
let isUserScrolling = ref(false)
let isAtTop = ref(true)
let isAtBottom = ref(false)
let terminalElement: HTMLElement
let pauseIcon = computed(() => {
    return isPaused.value ? 'fas fa-play' : 'fas fa-pause'
})

const togglePause = () => {
    isPaused.value = !isPaused.value
}

const scrollToBottom = () => {
    terminalElement.scrollTop = terminalElement.scrollHeight
}

const scrollToTop = () => {
    terminalElement.scrollTop = 0
}

let gcodeDisplay = computed(() => {
    if (isPaused.value) {
        // When paused, return only the gcode lines up to the last visible line
        return job.value?.gcode?.slice(0, lastVisibleLineIndex.value).join('\n') || ''
    } else if (job.value?.gcode) {
        // When not paused, return all the gcode lines and update the last visible line index
        lastVisibleLineIndex.value = job.value.gcode.length
        return job.value.gcode.join('\n') || ''
    } else {
        return ''
    }
})

let isModalVisible = ref(false)

onMounted(async () => {
    await nextTick()

    const modalElement = document.getElementById('gcodeLiveViewModal')
    terminalElement = document.querySelector('.gcode-display') as HTMLElement
    if (modalElement && terminalElement) {
        modalElement.addEventListener('shown.bs.modal', () => {
            terminalElement.scrollTop = terminalElement.scrollHeight
            isUserScrolling.value = false
            isModalVisible.value = true
        })

        modalElement.addEventListener('hidden.bs.modal', () => {
            isModalVisible.value = false
        })

        terminalElement.addEventListener('scroll', () => {
            // User is scrolling if they're not at the bottom
            isUserScrolling.value = terminalElement.scrollTop + terminalElement.clientHeight < terminalElement.scrollHeight

            // If the user has scrolled to the bottom, resume automatic scrolling
            if (terminalElement.scrollTop + terminalElement.clientHeight >= terminalElement.scrollHeight) {
                isUserScrolling.value = false
            }
            isAtTop.value = terminalElement.scrollTop === 0
            isAtBottom.value = terminalElement.scrollTop + terminalElement.clientHeight >= terminalElement.scrollHeight
        })

        // Watch the gcodeDisplay for changes and adjust the scroll position each time it changes
        watchEffect(() => {
            if (isModalVisible.value) {
                gcodeDisplay.value
                if (!isPaused.value && !isUserScrolling.value) {
                    terminalElement.scrollTop = terminalElement.scrollHeight
                } else if (!isPaused.value && isUserScrolling.value && terminalElement.scrollTop === 0) {
                    // If the user has scrolled to the top, show the first GCode line
                    terminalElement.scrollTop = 0
                }
            }
        })
    }
})
</script>

<template>
    <div>
        <div class="gcode-display-container">
            <pre class="gcode-display">{{ gcodeDisplay }}</pre>
            <div class="controls">
                <button class="btn btn-primary" v-on:click="scrollToTop" v-bind:disabled="isAtTop">
                    <i class="fas fa-arrow-up"></i>
                </button>
                <button class="btn btn-primary" v-on:click="togglePause">
                    <i :class="pauseIcon"></i>
                </button>
                <button class="btn btn-primary" v-on:click="scrollToBottom" v-bind:disabled="isAtBottom">
                    <i class="fas fa-arrow-down"></i>
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.gcode-display-container {
    position: relative;
}

.controls {
    position: absolute;
    bottom: 0;
    right: 10px;
    padding: 10px;
}

.controls .btn {
    margin: 5px;
    width: 40px;
    /* Adjust as needed */
    height: 40px;
    /* Adjust as needed */
    display: flex;
    align-items: center;
    justify-content: center;
}

.gcode-display {
    width: 100%;
    height: 200px;
    overflow: auto;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: .25rem;
    padding: .5rem;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin-top: 1rem;
}
</style>