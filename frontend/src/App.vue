<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

onMounted(() => auth.fetchUser())

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div id="app-shell">
    <header v-if="auth.isAuthenticated" class="app-nav">
      <div class="nav-left">
        <img src="/logo.png" alt="CareerPilot-AI" class="nav-logo-img" @click="router.push('/')" />
        <router-link to="/" class="nav-link" exact>首页</router-link>
        <router-link to="/history" class="nav-link">JD 历史</router-link>
        <router-link to="/memory" class="nav-link">记忆库</router-link>
      </div>
      <div class="nav-right">
        <span v-if="auth.user" class="nav-user">
          {{ auth.user.username }}
          <span class="nav-email">{{ auth.user.email }}</span>
        </span>
        <el-button size="small" text @click="handleLogout">退出登录</el-button>
      </div>
    </header>

    <main :class="{ 'no-nav': !auth.isAuthenticated }">
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
  margin: 0;
}

body {
  background: #f5f7fb;
  color: #1f2937;
  font-family:
    Inter,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    "Microsoft YaHei",
    sans-serif;
}

button,
input,
textarea,
select {
  font: inherit;
}
</style>

<style scoped>
.app-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 52px;
  background: #fff;
  border-bottom: 1px solid #dbe3ef;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-logo-img {
  height: 32px;
  cursor: pointer;
  vertical-align: middle;
}

.nav-logo {
  font-weight: 800;
  color: #2563eb;
  font-size: 16px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-user {
  color: #1f2937;
  font-size: 14px;
  font-weight: 500;
}

.nav-email {
  color: #667085;
  font-weight: 400;
  margin-left: 6px;
  font-size: 13px;
}

.nav-link {
  margin-left: 20px;
  color: #667085;
  text-decoration: none;
  font-size: 14px;
  transition: color .2s;
}
.nav-link:hover { color: #2563eb; }
.nav-link.router-link-active { color: #2563eb; font-weight: 600; }

.no-nav {
  min-height: 100vh;
}
</style>
