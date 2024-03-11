<script setup lang="ts">
import { nextTick, onMounted, onActivated, onDeactivated, ref, toRef, watchEffect } from 'vue';
import { useGetFile, type Job } from '@/model/jobs';
import * as GCodePreview from 'gcode-preview';

const { getFile } = useGetFile();

const props = defineProps({
    job: Object as () => Job
})
const job = toRef(props, 'job')
let lastProcessedLine = ref(0);

// Create a ref for the canvas
const canvas = ref<HTMLCanvasElement | null>(null);

let preview: GCodePreview.WebGLPreview | null = null;

onMounted(async () => {
    const modal = document.getElementById('gcodeLiveViewModal');
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    modal.addEventListener('shown.bs.modal', async () => {
        // Initialize the GCodePreview and show the GCode when the modal is shown
        if (canvas.value) {
            preview = GCodePreview.init({
                canvas: canvas.value,
                extrusionColor: 'hotpink',
                backgroundColor: 'black',
                buildVolume: { x: 250, y: 210, z: 220, r: 0, i: 0, j: 0 },
            });

            if (canvas.value) {
                try {
                    if (job.value?.gcode) {
                        console.log('job.value.gcode:', job.value.gcode);
                        preview?.processGCode(job.value.gcode); // MAIN LINE
                    }
                } catch (error) {
                    console.error('Failed to process GCode:', error);
                }
            } else {
                console.error('Canvas element is not available in showGCode');
            }
        }
    });

    watchEffect(() => {
        if (job.value?.gcode && preview) {
            const newLines = job.value.gcode.slice(lastProcessedLine.value);
            if (newLines.length > 0) {
                try {
                    preview.processGCode(newLines);
                    lastProcessedLine.value = job.value.gcode.length;
                } catch (error) {
                    console.error('Failed to process GCode:', error);
                }
            }
        }
    });

    modal.addEventListener('hidden.bs.modal', () => {
        // Clean up when the modal is hidden
        preview?.clear();
    });
});
</script>

<template>
        <canvas ref="canvas"></canvas>
</template>

<style scoped>
canvas {
    width: 100%;
    height: 100%;
    display: block;
}
</style>