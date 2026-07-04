import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type ApplicationRecord,
  type ApplicationCreate,
  type CooldownInfo,
  createApplication,
  listApplications,
  updateApplicationStatus,
  deleteApplication,
  checkCooldown,
} from '@/api'

export const useApplicationStore = defineStore('application', () => {
  const applications = ref<ApplicationRecord[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      applications.value = await listApplications()
    } finally {
      loading.value = false
    }
  }

  async function create(data: ApplicationCreate) {
    await createApplication(data)
    await fetchAll()
  }

  async function updateStatus(appId: number, status: string) {
    await updateApplicationStatus(appId, status)
    await fetchAll()
  }

  async function remove(appId: number) {
    await deleteApplication(appId)
    await fetchAll()
  }

  async function getCooldown(appId: number): Promise<CooldownInfo | null> {
    try {
      return await checkCooldown(appId)
    } catch {
      return null
    }
  }

  return { applications, loading, fetchAll, create, updateStatus, remove, getCooldown }
})
