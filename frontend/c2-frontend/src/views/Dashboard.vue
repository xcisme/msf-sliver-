<template>
  <el-container class="layout-container">
    <!-- 左侧导航 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="aside">
      <el-menu
        :default-active="activeIndex"
        :collapse="isCollapse"
        class="side-menu"
        background-color="#1e1e1e"
        text-color="#ffffff"
        active-text-color="#ffffff"
      >
        <el-menu-item index="1">
          <el-icon><Aim /></el-icon>
          <template #title>MSF工具</template>
        </el-menu-item>
        <el-menu-item index="2">
          <el-icon><Connection /></el-icon>
          <template #title>Sliver工具</template>
        </el-menu-item>
        <el-menu-item index="3">
          <el-icon><Link /></el-icon>
          <template #title>跨工具协同</template>
        </el-menu-item>
        <el-menu-item index="4">
          <el-icon><Document /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部状态栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-space>
            <el-button
              type="primary"
              link
              @click="isCollapse = !isCollapse"
              class="collapse-btn"
            >
              <el-icon>
                <Fold v-if="!isCollapse" />
                <Expand v-else />
              </el-icon>
            </el-button>
            <span class="welcome-text">欢迎回来，管理员</span>
          </el-space>
        </div>
        <div class="header-right">
          <span class="status-item">
            <span :class="['status-dot', backendStatus]"></span>
            <template v-if="backendStatus === 'checking'">
              正在检测...
            </template>
            <template v-else-if="backendStatus === 'connected'">
              后端已连接
            </template>
            <template v-else>
              后端未连接
            </template>
          </span>
          <span class="status-item">
            <span :class="['status-dot', msfStatus]"></span>
            <template v-if="msfStatus === 'checking'">
              正在检测...
            </template>
            <template v-else-if="msfStatus === 'connected'">
              MSF已连接 ({{ msfSessionsCount }}个会话)
            </template>
            <template v-else>
              MSF未连接
            </template>
          </span>
          <el-button
            type="primary"
            link
            :loading="isChecking"
            @click="handleCheckConnection"
          >
            {{ isChecking ? '检测中...' : '刷新状态' }}
          </el-button>
          <el-button type="primary" link>退出登录</el-button>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main">
        <div class="grid-container">
          <!-- 欢迎卡片 -->
          <el-card class="welcome-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>欢迎使用C2协同工具</span>
              </div>
            </template>
            <div class="card-content">
              <p class="intro-text">
                本系统是一个综合性的C2协同工具平台，集成Metasploit Framework和Sliver两大渗透测试框架，
                提供统一的操作界面和跨工具协同能力。您可以通过左侧导航菜单访问各项功能模块，
                实现漏洞利用、会话管理、横向移动等渗透测试操作。
              </p>
              <div class="action-buttons">
                <el-button type="primary">运行Exploit</el-button>
                <el-button>查看会话</el-button>
              </div>
            </div>
          </el-card>

          <!-- 会话列表卡片 -->
          <el-card class="sessions-card" shadow="hover" v-if="backendStatus === 'connected' && msfStatus === 'connected'">
            <template #header>
              <div class="card-header">
                <span>当前会话 ({{ sessions.length }}个)</span>
              </div>
            </template>
            <div class="table-wrapper">
              <el-empty v-if="!loadingSessions && sessions.length === 0" description="暂无会话" />
              <div v-else v-loading="loadingSessions" element-loading-background="#1a1a1a">
                <el-table :data="sessions">
                  <el-table-column prop="id" label="会话ID" width="100" />
                  <el-table-column prop="type" label="类型" width="80" />
                  <el-table-column prop="info" label="目标信息" />
                  <el-table-column label="操作" width="80" fixed="right">
                    <template #default="{ row }">
                      <el-button
                        type="danger"
                        size="small"
                        :loading="stopLoading[row.id]"
                        :disabled="stopLoading[row.id]"
                        @click="handleStopSession(row)"
                      >
                        结束
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>

          <!-- 操作日志卡片 -->
          <el-card class="logs-card" shadow="hover">
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <span style="font-weight: 500; color: #ffffff;">操作日志</span>
                <el-button size="small" @click="clearLogs">清空</el-button>
              </div>
            </template>
            <div class="timeline-wrapper">
              <el-timeline v-if="logs.length > 0">
                <el-timeline-item
                  v-for="(log, index) in logs"
                  :key="index"
                  :timestamp="log.time"
                  :color="log.result === 'success' ? '#67c23a' : '#f56c6c'"
                >
                  {{ log.action }}：{{ log.target }}
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无日志" :image-size="60" />
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Aim, Connection, Link, Document, Expand, Fold } from '@element-plus/icons-vue'
import { checkBackendHealth, testMsfConnection, getSessions, stopSession } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeIndex = ref('1')
const backendStatus = ref('checking')
const msfStatus = ref('checking')
const msfSessionsCount = ref(0)
const isChecking = ref(false)
const sessions = ref([])
const loadingSessions = ref(false)
const isCollapse = ref(false)
const stopLoading = ref({})
const logs = ref([])

const addLog = (action, target, result) => {
  const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logs.value.push({ time, action, target, result })

  // 限制日志最大条数为50条
  if (logs.value.length > 50) {
    logs.value.shift()
  }
}

const checkBackend = async () => {
  try {
    await checkBackendHealth()

    const wasDisconnected = backendStatus.value === 'disconnected'
    backendStatus.value = 'connected'

    if (wasDisconnected) {
      ElMessage.success('后端服务已恢复连接')
    }

    // 后端连接成功后检测MSF
    await checkMsf()

  } catch (error) {
    console.error('后端连接失败:', error)

    const wasConnected = backendStatus.value === 'connected'
    backendStatus.value = 'disconnected'
    msfStatus.value = 'disconnected'
    msfSessionsCount.value = 0
    sessions.value = []

    if (wasConnected) {
      ElMessage.error('后端服务连接断开')
    }
  }
}

const checkMsf = async () => {
  // 如果后端没连接，不检测MSF
  if (backendStatus.value !== 'connected') {
    msfStatus.value = 'disconnected'
    return
  }

  try {
    msfStatus.value = 'checking'
    const res = await testMsfConnection()

    // 根据返回结果判断
    if (res && res.status === 'success') {
      msfStatus.value = 'connected'
      msfSessionsCount.value = res.sessions_count || 0

      // 连接成功后自动获取会话列表
      await fetchSessions()
    } else {
      // API返回成功但status不是success
      msfStatus.value = 'disconnected'
      msfSessionsCount.value = 0
      sessions.value = []
    }

  } catch (error) {
    console.error('MSF连接失败:', error)

    // 记录旧状态，用于判断是否需要弹窗
    const wasConnected = msfStatus.value === 'connected'

    msfStatus.value = 'disconnected'
    msfSessionsCount.value = 0
    sessions.value = []

    // 只有从连接状态变为断开才弹窗
    if (wasConnected) {
      ElMessage.error('MSF连接已断开')
    }
  }
}

const fetchSessions = async () => {
  if (backendStatus.value !== 'connected') {
    return
  }

  loadingSessions.value = true
  try {
    const res = await getSessions()
    sessions.value = res.sessions || []

    // 能成功获取会话，说明MSF肯定在线
    if (msfStatus.value !== 'connected') {
      msfStatus.value = 'connected'
    }

  } catch (error) {
    console.error('获取会话列表失败:', error)

    // 关键修复：获取会话失败，说明MSF已断开
    // 只有当之前显示为connected时才需要更新状态并弹窗
    if (msfStatus.value === 'connected') {
      msfStatus.value = 'disconnected'
      sessions.value = []
      ElMessage.error('MSF连接已断开')
    }
  } finally {
    loadingSessions.value = false
  }
}

const handleCheckConnection = async () => {
  if (isChecking.value) return

  isChecking.value = true
  backendStatus.value = 'checking'
  msfStatus.value = 'checking'

  await checkBackend()

  isChecking.value = false
}

const handleStopSession = async (session) => {
  try {
    await ElMessageBox.confirm(
      `确定要结束会话 [${session.id}] 吗？`,
      '确认结束会话',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    // 设置加载状态
    stopLoading.value[session.id] = true

    await stopSession(session.id)

    ElMessage.success(`会话 ${session.id} 已结束`)

    // 记录日志
    addLog('结束会话', `会话 ${session.id}`, 'success')

    // 刷新会话列表
    await fetchSessions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('结束会话失败:', error)
      ElMessage.error('结束会话失败')

      // 记录失败日志
      addLog('结束会话', `会话 ${session.id}`, 'error')
    }
  } finally {
    // 移除加载状态
    stopLoading.value[session.id] = false
  }
}

const executeExploitHandler = async (exploitModule) => {
  if (backendStatus.value !== 'connected' || msfStatus.value !== 'connected') {
    ElMessage.error('MSF未连接，无法执行Exploit')
    return
  }

  try {
    ElMessage.info('开始执行Exploit...')
    // TODO: 调用实际的 executeExploit API
    // await executeExploit({ module: exploitModule })

    // 模拟执行成功
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success('Exploit执行成功')
    addLog('执行Exploit', exploitModule, 'success')

    // 刷新会话列表
    await fetchSessions()
  } catch (error) {
    console.error('执行Exploit失败:', error)
    ElMessage.error('Exploit执行失败')
    addLog('执行Exploit', exploitModule, 'error')
  }
}

const clearLogs = () => {
  logs.value = []
}

onMounted(() => {
  handleCheckConnection()
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  overflow: hidden;
}

.aside {
  background-color: #1e1e1e;
  overflow: hidden;
  transition: width 0.3s ease;
}

.side-menu {
  border-right: none;
  height: 100%;
}

.side-menu .el-menu-item.is-active {
  background-color: #333333 !important;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #252525;
  border-bottom: 1px solid #333333;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  padding: 8px;
}

.welcome-text {
  color: #ffffff;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #a0a0a0;
  font-size: 14px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.green {
  background-color: #67c23a;
}

.status-dot.connected {
  background-color: #67c23a;
}

.status-dot.disconnected {
  background-color: #f56c6c;
}

.status-dot.checking {
  background-color: #e6a23c;
}

.main {
  background-color: #1a1a1a;
  padding: 20px;
  overflow: hidden;
  height: calc(100vh - 60px);
}

.grid-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 20px;
  height: 100%;
}

.welcome-card {
  background-color: #252525;
  border: 1px solid #333333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.welcome-card :deep(.el-card__header) {
  background-color: #2a2a2a;
  border-bottom: 1px solid #333333;
  padding: 15px 20px;
  flex-shrink: 0;
}

.welcome-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
}

.sessions-card {
  background-color: #252525;
  border: 1px solid #333333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
  grid-column: 2;
  grid-row: 1 / 3;
}

.sessions-card :deep(.el-card__header) {
  background-color: #2a2a2a;
  border-bottom: 1px solid #333333;
  padding: 15px 20px;
  flex-shrink: 0;
}

.sessions-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.table-wrapper {
  height: 100%;
  overflow-y: auto;
  padding: 10px;
}

.sessions-card :deep(.el-table) {
  background-color: #252525;
}

.sessions-card :deep(.el-table th) {
  background-color: #2a2a2a;
  color: #a0a0a0;
}

.sessions-card :deep(.el-table td) {
  border-color: #333333;
  color: #e0e0e0;
}

.sessions-card :deep(.el-table tr:hover > td) {
  background-color: #2d2d2d !important;
}

.sessions-card :deep(.el-empty) {
  padding: 40px 0;
}

.sessions-card :deep(.el-empty__description p) {
  color: #666;
}

.logs-card {
  background-color: #252525;
  border: 1px solid #333333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.logs-card :deep(.el-card__header) {
  background-color: #2a2a2a;
  border-bottom: 1px solid #333333;
  padding: 15px 20px;
  flex-shrink: 0;
}

.logs-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.timeline-wrapper {
  height: 100%;
  overflow-y: auto;
  padding: 15px;
}

.logs-card :deep(.el-timeline-item__content) {
  color: #a0a0a0;
}

.logs-card :deep(.el-timeline-item__timestamp) {
  color: #666;
}

.logs-card :deep(.el-timeline) {
  padding: 0;
}

.card-header {
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  color: #a0a0a0;
}

.intro-text {
  line-height: 1.8;
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

/* 自定义滚动条样式 */
.table-wrapper::-webkit-scrollbar,
.timeline-wrapper::-webkit-scrollbar,
.welcome-card :deep(.el-card__body)::-webkit-scrollbar {
  width: 6px;
}

.table-wrapper::-webkit-scrollbar-track,
.timeline-wrapper::-webkit-scrollbar-track,
.welcome-card :deep(.el-card__body)::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.table-wrapper::-webkit-scrollbar-thumb,
.timeline-wrapper::-webkit-scrollbar-thumb,
.welcome-card :deep(.el-card__body)::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 3px;
}

.table-wrapper::-webkit-scrollbar-thumb:hover,
.timeline-wrapper::-webkit-scrollbar-thumb:hover,
.welcome-card :deep(.el-card__body)::-webkit-scrollbar-thumb:hover {
  background: #444;
}
</style>
