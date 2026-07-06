import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录 - CareerPilot-AI', guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { title: '注册 - CareerPilot-AI', guest: true },
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: () => import('@/views/KBView.vue'),
      meta: { title: '知识库 - CareerPilot-AI', requiresAuth: true },
    },
    {
      path: '/memory',
      name: 'memory',
      component: () => import('@/views/MemoryView.vue'),
      meta: { title: '记忆库 - CareerPilot-AI', requiresAuth: true },
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/JDHistoryView.vue'),
      meta: { title: '岗位描述库 - CareerPilot-AI', requiresAuth: true },
    },
    {
      path: '/',
      name: 'workspace',
      component: () => import('@/views/WorkspaceView.vue'),
      meta: { title: 'CareerPilot-AI 工作台', requiresAuth: true, key: 'workspace' },
    },
  ],
})

router.beforeEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : 'CareerPilot-AI'
  document.title = title

  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }

  if (to.meta.guest && token) {
    return { name: 'workspace' }
  }
})

export default router
