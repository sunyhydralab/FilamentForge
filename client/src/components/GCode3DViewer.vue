<script setup lang="ts">
import type { Job } from '@/model/jobs';
import * as THREE from 'three'
import { toRef } from 'vue';

const props = defineProps({
    job: Object as () => Job | null
})
const job = toRef(props, 'job')

// 3D VIEWER
const scene = new THREE.Scene()
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
const renderer = new THREE.WebGLRenderer()

renderer.setSize(window.innerWidth, window.innerHeight)
const gcodeViewerElement = document.getElementById('gcodeViewer')
if (gcodeViewerElement) {
    gcodeViewerElement.appendChild(renderer.domElement)
    renderer.setSize(gcodeViewerElement.clientWidth, gcodeViewerElement.clientHeight)
}
</script>

<template>
    <div>
        <div id="gcodeViewer" style="width: 100%; height: 400px;"></div>
    </div>
</template>

<style scoped></style>