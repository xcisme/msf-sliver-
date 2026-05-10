import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import AppLayout from '../views/AppLayout.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: AppLayout
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：已登录用户访问登录页跳转到仪表盘
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('c2_token')
  if (to.path === '/' && token) {
    next('/dashboard')
  } else if (to.path !== '/' && !token) {
    next('/')
  } else {
    next()
  }
})

export default router
