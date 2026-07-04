import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, getMe, type TokenResponse, type UserResponse } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserResponse | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const res: TokenResponse = await apiLogin(email, password)
      token.value = res.access_token
      user.value = { id: res.user_id, email: res.email, username: res.username }
      localStorage.setItem('token', res.access_token)
    } finally {
      loading.value = false
    }
  }

  async function register(email: string, username: string, password: string) {
    loading.value = true
    try {
      const res: TokenResponse = await apiRegister(email, username, password)
      token.value = res.access_token
      user.value = { id: res.user_id, email: res.email, username: res.username }
      localStorage.setItem('token', res.access_token)
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      user.value = await getMe()
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, loading, isAuthenticated, login, register, fetchUser, logout }
})
