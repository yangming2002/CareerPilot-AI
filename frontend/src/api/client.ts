import axios from 'axios'
import { ElMessage } from 'element-plus'

// In dev mode, Vite proxies /api/ to localhost:8001
// In production (Docker), nginx proxies /api/ to backend:8001
// Use relative URL so both work without config changes
const client = axios.create({
  baseURL: import.meta.env.PROD ? '' : 'http://localhost:8001',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      const path = window.location.pathname
      if (path !== '/login' && path !== '/register') {
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    let msg = ''
    const detail = error.response?.data?.detail

    if (typeof detail === 'string' && detail) {
      msg = detail
    } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      msg = '网络连接失败，请检查后端服务是否已启动。'
    } else if (error.code === 'ECONNABORTED') {
      msg = '请求超时，请稍后重试。'
    } else {
      msg = '请求失败，请稍后重试。'
    }

    if (msg) {
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  },
)

export default client
