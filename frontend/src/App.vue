<script setup lang="ts">
import { onMounted, ref } from 'vue'
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

const navItems = [
  { path: '/', label: '工作台', icon: '⚡' },
  { path: '/history', label: '岗位描述', icon: '📋' },
  { path: '/knowledge', label: '知识库', icon: '📚' },
  { path: '/memory', label: '记忆库', icon: '🧠' },
]
</script>

<template>
  <div id="app-shell" :class="{ 'no-sidebar': !auth.isAuthenticated }">
    <aside v-if="auth.isAuthenticated" class="sidebar">
      <div class="side-logo" @click="router.push('/')">
        <img src="/logo.png" alt="CareerPilot-AI" class="logo-img" />
      </div>

      <nav class="side-nav">
        <router-link
          v-for="item in navItems" :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path || (item.path === '/' && route.path.startsWith('/workspace')) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </nav>

      <div class="side-footer">
        <div class="user-info" v-if="auth.user">
          <span class="user-avatar">{{ auth.user.username[0] }}</span>
          <div>
            <div class="user-name">{{ auth.user.username }}</div>
            <div class="user-email">{{ auth.user.email }}</div>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">退出</button>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #app {
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
  background: #f8f9fb;
  color: #1a1a2e;
  -webkit-font-smoothing: antialiased;
}

body { overflow: hidden; }

button, input, textarea, select { font: inherit; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 10px; }
</style>

<style scoped>
#app-shell { display: flex; height: 100vh; }
#app-shell.no-sidebar { display: block; }

.sidebar {
  width: 220px;
  background: #111827;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.side-logo {
  padding: 16px;
  cursor: pointer;
  background: #fff;
  margin: 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.logo-img { height: 36px; object-fit: contain; }

.side-nav {
  flex: 1;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #9ca3af;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all .15s;
}

.nav-item:hover { background: #1f2937; color: #f3f4f6; }
.nav-item.active { background: #2563eb; color: #fff; }

.nav-icon { font-size: 16px; }

.side-footer {
  padding: 16px;
  border-top: 1px solid #1f2937;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.user-avatar {
  width: 32px; height: 32px;
  border-radius: 8px;
  background: #374151;
  color: #e5e7eb;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: 14px;
  flex-shrink: 0;
}

.user-name { font-size: 13px; font-weight: 600; color: #f3f4f6; }
.user-email { font-size: 11px; color: #6b7280; margin-top: 1px; }

.logout-btn {
  width: 100%; padding: 8px;
  border: 1px solid #374151; border-radius: 6px;
  background: transparent; color: #9ca3af;
  font-size: 12px; cursor: pointer;
  transition: all .15s;
}
.logout-btn:hover { background: #1f2937; color: #f3f4f6; }

.main-content {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}
</style>
