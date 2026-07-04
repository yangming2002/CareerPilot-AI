import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type InterviewRecord,
  type InterviewCreate,
  createInterview,
  listInterviews,
} from '@/api'

export const useInterviewStore = defineStore('interview', () => {
  const reviews = ref<InterviewRecord[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      reviews.value = await listInterviews()
    } finally {
      loading.value = false
    }
  }

  async function create(data: InterviewCreate) {
    await createInterview(data)
    await fetchAll()
  }

  return { reviews, loading, fetchAll, create }
})
