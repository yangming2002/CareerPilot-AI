<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const password2 = ref('')
const loading = ref(false)

async function handleRegister() {
  if (!username.value.trim() || !email.value.trim() || !password.value) {
    ElMessage.warning('请填写所有字段')
    return
  }
  if (!email.value.includes('@')) {
    ElMessage.warning('请输入有效的邮箱地址')
    return
  }
  if (password.value !== password2.value) {
    ElMessage.warning('两次密码不一致')
    return
  }
  if (password.value.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  loading.value = true
  try {
    await auth.register(email.value, username.value, password.value)
    ElMessage.success('注册成功')
    router.push('/')
  } catch {
    // Error toast already shown by axios interceptor
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
        <p>创建你的求职工作台账号</p>
      </div>

      <el-form label-position="top" size="large" @submit.prevent="handleRegister">
        <el-form-item label="用户名">
          <el-input
            v-model="username"
            placeholder="给自己起个名字"
            autocomplete="name"
          />
        </el-form-item>

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
            placeholder="至少 6 位"
            autocomplete="new-password"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码">
          <el-input
            v-model="password2"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
            show-password
          />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          native-type="submit"
          style="width: 100%"
        >
          注册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
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
