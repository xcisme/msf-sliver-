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
          <el-empty v-if="!loadingSessions && sessions.length === 0" description="暂无会话" />
          <div v-else v-loading="loadingSessions" element-loading-background="#1a1a1a">
            <el-table :data="sessions">
              <el-table-column prop="id" label="会话ID" width="120" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="info" label="目标信息" />
              <el-table-column prop="platform" label="平台" width="100" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag type="success" size="small">活跃</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Aim, Connection, Link, Document, Expand, Fold } from '@element-plus/icons-vue'
import { checkBackendHealth, testMsfConnection, getSessions } from '../api'
import { ElMessage } from 'element-plus'

const activeIndex = ref('1')
const backendStatus = ref('checking')
const msfStatus = ref('checking')
const msfSessionsCount = ref(0)
const isChecking = ref(false)
const sessions = ref([])
const loadingSessions = ref(false)
const isCollapse = ref(false)

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
  overflow-y: auto;
  max-height: calc(100vh - 60px);
}

.welcome-card {
  background-color: #252525;
  border: 1px solid #333333;
  max-width: 800px;
  margin-bottom: 20px;
  border-radius: 8px;
}

.welcome-card :deep(.el-card__header) {
  background-color: #2a2a2a;
  border-bottom: 1px solid #333333;
  padding: 18px 20px;
}

.sessions-card {
  background-color: #252525;
  border: 1px solid #333333;
  max-width: 800px;
  border-radius: 8px;
}

.sessions-card :deep(.el-card__header) {
  background-color: #2a2a2a;
  border-bottom: 1px solid #333333;
  padding: 18px 20px;
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

.card-header {
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
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
.main::-webkit-scrollbar {
  width: 8px;
}

.main::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.main::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 4px;
}

.main::-webkit-scrollbar-thumb:hover {
  background: #444;
}
</style>
