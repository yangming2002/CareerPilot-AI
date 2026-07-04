import { defineStore } from 'pinia'
import { ref } from 'vue'
import { type SkillProfile, getSkillProfile } from '@/api'

export const useSkillProfileStore = defineStore('skillProfile', () => {
  const profile = ref<SkillProfile | null>(null)
  const loading = ref(false)

  async function fetchProfile() {
    loading.value = true
    try {
      profile.value = await getSkillProfile()
    } finally {
      loading.value = false
    }
  }

  return { profile, loading, fetchProfile }
})
