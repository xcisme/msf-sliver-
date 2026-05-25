import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('c2_token')
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

    // 处理 401 错误
    if (error.response && error.response.status === 401) {
      // 清除本地 token
      localStorage.removeItem('c2_token')

      // 提示用户登录已过期
      console.warn('登录已过期，请重新登录')

      // 跳转到登录页（如果当前不在登录页）
      const currentPath = window.location.pathname
      if (currentPath !== '/' && currentPath !== '/login') {
        window.location.href = '/login'
      } else if (currentPath === '/') {
        window.location.href = '/'
      }
    }

    return Promise.reject(error)
  }
)

// ==================== 真实接口 ====================

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

// 获取 MSF 会话列表
export const getMsfSessions = () => {
  return request.get('/api/msf/sessions')
}

// 获取最近操作日志
export const getRecentLogs = (limit = 5) => {
  return request.get('/api/logs/recent', { params: { limit } })
}

// 获取工具链接状态
export const getLinkStatus = () => {
  return request.get('/api/status/links')
}

// 获取模块列表
export const getModules = (type = 'exploit', keyword = '') => {
  return request.get('/api/msf/modules', { params: { type, keyword } })
}

// 获取模块的兼容 payloads
export const getCompatiblePayloads = (moduleName) => {
  return request.get('/api/msf/modules/compatible_payloads', { params: { module_name: moduleName } })
}

// 获取模块参数
export const getModuleOptions = (moduleName, payload = null) => {
  const params = { module_name: moduleName }
  if (payload) params.payload = payload
  return request.get('/api/msf/modules/options', { params })
}

export const checkBackendHealth = () => {
  return request.get('/api/health')
}

export const stopSession = (sessionId) => {
  return request.delete(`/api/msf/session/${sessionId}`)
}

// 获取 Sliver 会话列表
export const getSliverSessions = () => {
  return request.get('/api/sliver/sessions')
}

// 向 Sliver 会话发送命令
export const sendSliverCommand = (sessionId, command) => {
  return request.post(`/api/sliver/session/${sessionId}/command`, { command })
}

// 删除 Sliver 会话
export const deleteSliverSession = (sessionId) => {
  return request.delete(`/api/sliver/session/${sessionId}`)
}

// 生成 Implant
export const generateImplant = (params) => {
  return request.post('/api/sliver/implant/generate', params)
}

// 获取自动推送配置
export const getAutoPush = () => {
  return request.get('/api/coordination/auto-push')
}

// 设置自动推送开关
export const setAutoPush = (enabled) => {
  return request.put('/api/coordination/auto-push', { enabled })
}

// 获取MSF会话列表（用于手动植入下拉框）
export const getMsfSessionsForManual = () => {
  return request.get('/api/coordination/msf-sessions')
}

// 手动植入Sliver
export const manualImplant = (msfSessionId, implantConfig = {}) => {
  return request.post('/api/coordination/implant', { msf_session_id: msfSessionId, implant_config: implantConfig })
}

// 获取会话映射表
export const getMappings = () => {
  return request.get('/api/coordination/mappings')
}

// 删除映射
export const deleteMapping = (id) => {
  return request.delete(`/api/coordination/mapping/${id}`)
}

// 重连映射
export const reconnectMapping = (id) => {
  return request.post(`/api/coordination/mapping/${id}/reconnect`)
}

// IP池管理
export const getIpPool = () => {
  return request.get('/api/config/ip-pool')
}

export const addIp = (ipAddress, description = '') => {
  return request.post('/api/config/ip-pool', { ip_address: ipAddress, description })
}

export const deleteIp = (id) => {
  return request.delete(`/api/config/ip-pool/${id}`)
}

export const testRandomIp = () => {
  return request.post('/api/config/ip-pool/test')
}

// 域名动态解析配置
export const getDomainDnsConfig = () => {
  return request.get('/api/config/domain-dns')
}

export const updateDomainDnsConfig = (data) => {
  return request.put('/api/config/domain-dns', data)
}

export const manualUpdateDns = () => {
  return request.post('/api/config/domain-dns/manual-update')
}

// 流量混淆设置
export const getTrafficConfig = () => {
  return request.get('/api/config/traffic')
}

export const updateTrafficConfig = (data) => {
  return request.put('/api/config/traffic', data)
}

// 获取日志列表（支持筛选、分页）
export const getLogs = (params) => {
  return request.get('/api/logs', { params })
}

// 获取操作类型列表
export const getLogActions = () => {
  return request.get('/api/logs/actions')
}

// ==================== 任务管理接口 ====================

export const getTasks = (params) => {
  return request.get('/api/msf/tasks', { params })
}

export const createTask = (data) => {
  return request.post('/api/msf/tasks', data)
}

export const deleteTaskApi = (id) => {
  return request.delete(`/api/msf/tasks/${id}`)
}

export const stopTask = (id) => {
  return request.post(`/api/msf/tasks/${id}/stop`)
}

export const getTask = (id) => {
  return request.get(`/api/msf/tasks/${id}`)
}

export default request
