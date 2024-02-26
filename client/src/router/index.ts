import { createRouter, createWebHashHistory } from 'vue-router'
import MainView from '@/views/MainView.vue'
import QueueViewVue from '@/views/QueueView.vue'
import RegisteredViewVue from '@/views/RegisteredView.vue'
import SubmitJobVue from '@/views/SubmitJob.vue'
import JobHistoryVue from '@/views/JobHistory.vue'

const routes = [
  {
    path: '/',
    name: 'MainView',
    component: MainView
  },
  {
    path: '/queue',
    name: 'QueueViewVue',
    component: QueueViewVue
  },
  {
    path: '/registration',
    name: 'RegisteredViewVue',
    component: RegisteredViewVue
  },
  {
    path: '/submit',
    name: 'SubmitJobVue',
    component: SubmitJobVue
  },
  {
    path: '/history',
    name: 'JobHistoryVue',
    component: JobHistoryVue
  }, 
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
