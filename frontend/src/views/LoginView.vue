<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!email.value.trim() || !password.value) {
    ElMessage.warning('请填写邮箱和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    ElMessage.success('登录成功')
    router.push('/')
  } catch { } finally { loading.value = false }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <img src="/logo.png" alt="CareerPilot-AI" class="auth-logo" />
      <h2>登录</h2>
      <p class="auth-sub">Agent 驱动求职工作台</p>
      <el-form label-position="top" size="large" @submit.prevent="handleLogin">
        <el-form-item label="邮箱">
          <el-input v-model="email" type="email" placeholder="your@email.com" autocomplete="email" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="输入密码" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" native-type="submit" class="submit-btn">登录</el-button>
      </el-form>
      <p class="auth-foot">还没有账号？<router-link to="/register">注册</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; background: #f8f9fb;
}

.auth-card {
  width: 400px; padding: 44px 40px;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 16px;
}

.auth-logo { height: 32px; margin-bottom: 24px; }

h2 { font-size: 22px; font-weight: 700; color: #111827; margin-bottom: 4px; }

.auth-sub { color: #6b7280; font-size: 14px; margin-bottom: 32px; }

.submit-btn { width: 100%; height: 44px; border-radius: 10px; font-weight: 600; }

.auth-foot { margin-top: 20px; text-align: center; font-size: 13px; color: #6b7280; }
.auth-foot a { color: #2563eb; text-decoration: none; font-weight: 500; }
</style>
