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
  if (!email.value || !password.value) {
    ElMessage.warning('请填写邮箱和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '登录失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h1>CareerPilot-AI</h1>
        <p>登录你的求职工作台</p>
      </div>

      <el-form label-position="top" size="large" @submit.prevent="handleLogin">
        <el-form-item label="邮箱">
          <el-input
            v-model="email"
            type="email"
            placeholder="your@email.com"
            autocomplete="email"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="输入密码"
            autocomplete="current-password"
            show-password
          />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          native-type="submit"
          style="width: 100%"
        >
          登录
        </el-button>
      </el-form>

      <div class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fb;
}

.auth-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-header h1 {
  margin-bottom: 8px;
  color: #2563eb;
  font-size: 24px;
}

.auth-header p {
  color: #667085;
  font-size: 14px;
}

.auth-footer {
  margin-top: 20px;
  text-align: center;
  color: #667085;
  font-size: 14px;
}

.auth-footer a {
  color: #2563eb;
  text-decoration: none;
}
</style>
