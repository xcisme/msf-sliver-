import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 15000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('c2_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        // 清除本地 token
        localStorage.removeItem('c2_token')

        // 提示用户登录已过期
        // 注意：ElMessage 需要在 Vue 应用上下文才能显示，这里仅作提示
        console.warn('登录已过期，请重新登录')

        // 跳转到登录页（如果当前不在登录页）
        const currentPath = window.location.pathname
        if (currentPath !== '/' && currentPath !== '/login') {
          window.location.href = '/login'
        } else if (currentPath === '/') {
          window.location.href = '/'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default request
