import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 临时方案：优先使用 localStorage 中的 token，如果没有则使用默认 token
    // TODO: 上线前移除默认 token
    const token = localStorage.getItem('token') || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3Mjg2NzYzN30.N405_6VY2HEiT8TwAWx8LTjgbFF2jhos3TeLyA-zIaA'
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API 函数
export const testMsfConnection = () => {
  return request.get('/api/msf/test')
}

export const login = (username, password) => {
  return request.post('/api/auth/login', { username, password })
}

export const getSessions = () => {
  return request.get('/api/msf/sessions')
}

export const executeExploit = (data) => {
  return request.post('/api/msf/exploit', data)
}

export const checkBackendHealth = () => {
  return request.get('/api/health')
}

export default request
