<script setup lang="ts">
import { onMounted, ref } from 'vue'
import * as THREE from 'three'
import type { Job } from '@/model/jobs';

const props = defineProps({
  job: Object as () => Job | null
})

const job = ref(props.job)

onMounted(() => {
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer()

    renderer.setSize(window.innerWidth, window.innerHeight)
    const gcodeViewerElement = document.getElementById('gcodeViewer')
    if (gcodeViewerElement) {
        gcodeViewerElement.appendChild(renderer.domElement)
        renderer.setSize(gcodeViewerElement.clientWidth, gcodeViewerElement.clientHeight)
    }

    // Parse GCode into a format that Three.js can understand
    // This is a simplified example and may not work for all GCode
    console.log(job.value?.gcode)
})
</script>

<template>
    <div id="gcodeViewer" style="width: 100%; height: 400px;"></div>
</template>

<style scoped>
#gcodeViewer {
    width: 100%;
    height: 400px;
}
</style>