import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
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

// ==================== 模拟接口 ====================

// 模拟数据存储
const mockData = {
  msfSessions: [
    { id: 'S001', host: '192.168.1.100', user: 'root', os: 'Linux ubuntu 5.4' },
    { id: 'S002', host: '192.168.1.105', user: 'Administrator', os: 'Windows Server 2019' },
    { id: 'S003', host: '10.0.0.50', user: 'kali', os: 'Linux kali 5.10' }
  ],
  sliverSessions: [
    { id: 'SLV001', host: '192.168.1.100', user: 'root', os: 'Linux ubuntu 5.4' },
    { id: 'SLV002', host: '192.168.1.105', user: 'Administrator', os: 'Windows Server 2019' }
  ],
  recentLogs: [
    { time: '14:35:22', action: '执行Exploit', target: 'exploit/windows/smb/ms17_010_eternalblue', result: 'success' },
    { time: '14:30:15', action: '新建会话', target: '192.168.1.100', result: 'success' },
    { time: '14:25:08', action: '执行命令', target: 'whoami', result: 'success' },
    { time: '14:20:45', action: '结束会话', target: 'session_3', result: 'success' },
    { time: '14:15:30', action: '执行Exploit', target: 'exploit/multi/handler', result: 'error' }
  ],
  msfModules: [
    { name: 'exploit/windows/smb/ms17_010_eternalblue', description: '永恒之蓝漏洞利用', rank: 'great' },
    { name: 'exploit/multi/handler', description: 'Multi/Handler payload监听器', rank: 'great' },
    { name: 'exploit/linux/samba/is_known_pipename', description: 'Samba pipe_name利用', rank: 'good' },
    { name: 'exploit/misc/java_rmi_server', description: 'Java RMI服务器漏洞', rank: 'normal' },
    { name: 'auxiliary/scanner/http/title', description: 'HTTP标题扫描', rank: 'normal' }
  ],
  msfModuleOptions: {
    'exploit/windows/smb/ms17_010_eternalblue': [
      { name: 'RHOSTS', type: 'address', required: true, description: '目标IP或CIDR' },
      { name: 'RPORT', type: 'port', required: false, description: '目标端口', default: '445' },
      { name: 'PAYLOAD', type: 'enum', required: true, description: 'Payload类型' },
      { name: 'LHOST', type: 'address', required: true, description: '监听IP' },
      { name: 'LPORT', type: 'port', required: true, description: '监听端口', default: '4444' }
    ]
  },
  autoPush: false,
  mappings: [
    { id: 1, msfSessionId: 'S001', sliverSessionId: 'SLV001', implantTime: '2024-01-15 14:30:25', status: '已连接' },
    { id: 2, msfSessionId: 'S002', sliverSessionId: '', implantTime: '2024-01-15 15:20:10', status: '连接中' },
    { id: 3, msfSessionId: 'S003', sliverSessionId: 'SLV003', implantTime: '2024-01-15 16:45:30', status: '已断开' }
  ],
  ipPool: ['1.1.1.1', '2.2.2.2', '3.3.3.3'],
  domainConfig: {
    domain: 'example.com',
    currentIp: '93.184.216.34',
    updateInterval: 5
  },
  trafficConfig: {
    encryption: 'aes-256-cbc',
    randomHeaders: true,
    dataFragmentation: false
  },
  auditLogs: [
    { time: '2024-01-15 14:35:22', user: 'admin', operationType: 'exploit', target: 'exploit/windows/smb/ms17_010_eternalblue', result: '成功' },
    { time: '2024-01-15 14:30:15', user: 'admin', operationType: 'login', target: '192.168.1.10', result: '成功' },
    { time: '2024-01-15 14:25:08', user: 'admin', operationType: 'command', target: 'whoami', result: '成功' },
    { time: '2024-01-15 14:20:45', user: 'admin', operationType: 'stop_session', target: 'session_3', result: '成功' },
    { time: '2024-01-15 14:15:30', user: 'admin', operationType: 'implant', target: 'S001 -> SLV001', result: '成功' },
    { time: '2024-01-15 14:10:20', user: 'admin', operationType: 'exploit', target: 'exploit/multi/handler', result: '失败' },
    { time: '2024-01-15 14:05:10', user: 'admin', operationType: 'command', target: 'ipconfig', result: '成功' },
    { time: '2024-01-15 14:00:05', user: 'admin', operationType: 'delete', target: '任务 T001', result: '成功' },
    { time: '2024-01-15 13:55:30', user: 'admin', operationType: 'login', target: '192.168.1.10', result: '成功' },
    { time: '2024-01-15 13:50:15', user: 'admin', operationType: 'command', target: 'cat /etc/passwd', result: '失败' }
  ]
}

// 模拟命令回显
const mockCommandOutputs = {
  'whoami': 'root',
  'id': 'uid=0(root) gid=0(root) groups=0(root)',
  'pwd': '/root',
  'ls': 'Desktop  Documents  Downloads  Music  Pictures  Public  Templates  Videos',
  'uname -a': 'Linux ubuntu 5.4.0--generic #18-Ubuntu SMP x86_64 GNU/Linux',
  'ip addr': 'eth0: inet 192.168.1.100/24\nlo: inet 127.0.0.1/8',
  'cat /etc/passwd': 'root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin'
}

// 延迟函数
const delay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms))

// ==================== 模拟接口实现 ====================

/**
 * 获取MSF会话列表
 * 真实接口: GET /api/msf/sessions
 */
// getMsfSessions 已在真实接口区域定义

/**
 * 获取最近操作日志
 * 真实接口: GET /api/logs/recent
 */
// getRecentLogs 已在真实接口区域定义

/**
 * 获取MSF模块列表
 * 真实接口: GET /api/msf/modules
 * @param {string} type - 模块类型
 * @param {string} keyword - 搜索关键词
 */
export const getMsfModules = async (type = '', keyword = '') => {
  await delay()
  let modules = [...mockData.msfModules]
  if (keyword) {
    modules = modules.filter(m =>
      m.name.toLowerCase().includes(keyword.toLowerCase()) ||
      m.description.toLowerCase().includes(keyword.toLowerCase())
    )
  }
  return { modules }
}

/**
 * 获取MSF模块选项
 * 真实接口: GET /api/msf/module/:name/options
 * @param {string} moduleName - 模块名称
 */
export const getMsfModuleOptions = async (moduleName) => {
  await delay()
  const options = mockData.msfModuleOptions[moduleName] || []
  return { options }
}

/**
 * 执行Exploit
 * 真实接口: POST /api/msf/exploit
 * @param {object} data - 攻击参数
 */
export const runExploit = async (data) => {
  await delay(1000)
  const success = Math.random() > 0.3
  return {
    success,
    taskId: `T00${Date.now()}`,
    message: success ? 'Exploit执行成功' : 'Exploit执行失败',
    sessionId: success ? `S00${Math.floor(Math.random() * 10) + 1}` : null
  }
}

/**
 * 发送Sliver命令
 * 真实接口: POST /api/sliver/execute
 * @param {string} sessionId - 会话ID
 * @param {string} command - 命令
 */
// sendSliverCommand 已在真实接口区域定义

/**
 * 生成Implant
 * 真实接口: POST /api/sliver/generate
 * @param {object} params - 生成参数
 */
// generateImplant 已在真实接口区域定义

/**
 * 获取IP池
 * 真实接口: GET /api/advanced/ip-pool
 */
// getIpPool 已在真实接口区域定义

/**
 * 添加IP到池
 * 真实接口: POST /api/advanced/ip-pool
 * @param {string} ip - IP地址
 */
// addIp 已在真实接口区域定义

/**
 * 从池中删除IP
 * 真实接口: DELETE /api/advanced/ip-pool/:ip
 * @param {string} ip - IP地址
 */
// deleteIp 已在真实接口区域定义

/**
 * 随机测试IP
 * 真实接口: POST /api/advanced/ip-pool/random-test
 */
// testRandomIp 已在真实接口区域定义

/**
 * 获取域名DNS配置
 * 真实接口: GET /api/advanced/domain
 */
// getDomainDnsConfig 已在真实接口区域定义

/**
 * 更新域名DNS配置
 * 真实接口: POST /api/advanced/domain
 * @param {object} config - 配置对象
 */
// updateDomainDnsConfig 已在真实接口区域定义

/**
 * 手动更新DNS
 * 真实接口: POST /api/advanced/domain/update
 */
// manualUpdateDns 已在真实接口区域定义

/**
 * 获取流量混淆配置
 * 真实接口: GET /api/advanced/obfuscation
 */
// getTrafficConfig 已在真实接口区域定义

/**
 * 更新流量混淆配置
 * 真实接口: POST /api/advanced/obfuscation
 * @param {object} config - 配置对象
 */
// updateTrafficConfig 已在真实接口区域定义

/**
 * 获取审计日志
 * 真实接口: GET /api/logs
 * @param {object} params - 查询参数
 */
// getLogs 已在真实接口区域定义

export default request
