import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default client
