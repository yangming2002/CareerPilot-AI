import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type WrittenTestRecord,
  type WrittenTestCreate,
  createWrittenTest,
  listWrittenTests,
} from '@/api'

export const useWrittenTestStore = defineStore('writtenTest', () => {
  const reviews = ref<WrittenTestRecord[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      reviews.value = await listWrittenTests()
    } finally {
      loading.value = false
    }
  }

  async function create(data: WrittenTestCreate) {
    await createWrittenTest(data)
    await fetchAll()
  }

  return { reviews, loading, fetchAll, create }
})
