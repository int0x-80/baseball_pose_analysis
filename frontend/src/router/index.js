import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '../utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Training',
    component: () => import('../views/Training.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/:recordId',
    name: 'AnalysisDetail',
    component: () => import('../views/AnalysisDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/daily-records/:date',
    name: 'DailyRecords',
    component: () => import('../views/DailyRecords.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/trend',
    name: 'TrendPage',
    component: () => import('../views/TrendPage.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = auth.isLoggedIn()
  
  if (to.meta.requiresAuth && !isLoggedIn) {
    // 需要登录但未登录，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && isLoggedIn) {
    // 已登录但访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router
