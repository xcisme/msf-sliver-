<template>
  <div class="dashboard" v-loading="loading">
    <!-- 欢迎语 -->
    <div class="welcome-section">
      <h2>欢迎回来，管理员</h2>
      <el-button text @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon msf-icon">
            <el-icon><Aim /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ msfSessionCount }}</div>
            <div class="stat-label">MSF会话数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon sliver-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ sliverSessionCount }}</div>
            <div class="stat-label">Sliver会话数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon status-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              <span :class="['status-text', systemStatus === 'normal' ? 'normal' : 'abnormal']">
                {{ systemStatus === 'normal' ? '正常' : '异常' }}
              </span>
            </div>
            <div class="stat-label">系统状态</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 内容区域 -->
    <div class="content-row">
      <!-- 最近操作日志 -->
      <el-card class="log-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>最近操作日志</span>
          </div>
        </template>
        <el-timeline v-if="recentLogs.length > 0">
          <el-timeline-item
            v-for="(log, index) in recentLogs"
            :key="index"
            :timestamp="formatTime(log.time || log.created_at)"
            :color="getLogColor(log.result)"
          >
            {{ log.action }}：{{ log.target }}
          </el-timeline-item>
        </el-timeline>
        <div v-else class="empty-tip">暂无操作日志</div>
      </el-card>

      <!-- 工具链接状态 -->
      <el-card class="link-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>工具链接状态</span>
          </div>
        </template>
        <div class="link-list">
          <div class="link-item" v-for="(item, key) in linkStatus" :key="key">
            <div class="link-info">
              <span :class="['status-dot', getLinkStatusClass(item.status)]"></span>
              <span class="link-name">{{ getLinkName(key) }}</span>
            </div>
            <div class="link-status">
              {{ getLinkDisplay(item) }}
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Aim, Connection, CircleCheck, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getMsfSessions, getSliverSessions, getRecentLogs, getLinkStatus } from '../api'

// 统计数据
const msfSessionCount = ref(0)
const sliverSessionCount = ref(0)
const systemStatus = ref('normal')

// 最近日志
const recentLogs = ref([])

// 工具链接状态
const linkStatus = ref({})

// 加载状态
const loading = ref(false)

// 获取MSF会话数
const fetchMsfSessions = async () => {
  try {
    const res = await getMsfSessions()
    msfSessionCount.value = res.sessions?.length || res.data?.length || 0
  } catch (error) {
    console.error('获取MSF会话失败:', error)
    msfSessionCount.value = 0
  }
}

// 获取Sliver会话数
const fetchSliverSessions = async () => {
  try {
    const res = await getSliverSessions()
    sliverSessionCount.value = Array.isArray(res) ? res.length : (res.sessions?.length || res.data?.length || 0)
  } catch (error) {
    console.error('获取Sliver会话失败:', error)
    sliverSessionCount.value = 0
  }
}

// 获取最近日志
const fetchRecentLogs = async () => {
  try {
    const res = await getRecentLogs(5)
    console.log('Recent logs response:', res)
    // 后端返回数组直接使用
    if (Array.isArray(res)) {
      recentLogs.value = res
    } else if (res.logs) {
      recentLogs.value = res.logs
    } else if (res.data && Array.isArray(res.data)) {
      recentLogs.value = res.data
    } else if (res.data && res.data.items) {
      recentLogs.value = res.data.items
    } else {
      recentLogs.value = []
      console.warn('Unexpected response format:', res)
    }
    console.log('Processed recentLogs:', recentLogs.value)
  } catch (error) {
    console.error('获取最近日志失败:', error)
    recentLogs.value = []
  }
}

// 获取工具链接状态
const fetchLinkStatus = async () => {
  try {
    const res = await getLinkStatus()
    linkStatus.value = res.data || res || {}
    // 根据 MSF 连接状态判断系统状态
    const msfStatus = linkStatus.value.msf_rpc?.status || linkStatus.value.msf?.status
    systemStatus.value = (msfStatus === 'connected') ? 'normal' : 'abnormal'
  } catch (error) {
    console.error('获取工具链接状态失败:', error)
    linkStatus.value = {}
    systemStatus.value = 'abnormal'
  }
}

// 加载所有数据
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchMsfSessions(),
      fetchSliverSessions(),
      fetchRecentLogs(),
      fetchLinkStatus()
    ])
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await loadData()
  ElMessage.success('数据已刷新')
}

// 获取日志颜色
const getLogColor = (result) => {
  if (result === 'success' || result === '成功') return '#67c23a'
  if (result === 'failed' || result === '失败') return '#f56c6c'
  return '#909399'  // unknown/pending
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  if (typeof time === 'string') {
    try {
      const date = new Date(time)
      return date.toLocaleString('zh-CN')
    } catch {
      return time
    }
  }
  return String(time)
}

// 获取链接状态样式
const getLinkStatusClass = (status) => {
  if (status === 'connected') return 'connected'
  return 'disconnected'
}

// 获取链接名称
const getLinkName = (key) => {
  const map = {
    msf_rpc: 'MSF RPC',
    msf: 'MSF RPC',
    sliver_grpc: 'Sliver gRPC',
    sliver: 'Sliver gRPC',
    ip_pool: 'IP池轮换',
    ip_pool_status: 'IP池轮换'
  }
  return map[key] || key
}

// 获取链接显示信息
const getLinkDisplay = (item) => {
  if (item.status === 'connected') {
    return item.port ? `已连接 (端口${item.port})` : '已连接'
  }
  if (item.status === 'not_configured') {
    return '未配置'
  }
  return '未连接'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100%;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.welcome-section h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

/* 统计卡片行 */
.stats-row {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  border-radius: 16px;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.msf-icon {
  background-color: #e6f7ff;
  color: #1890ff;
}

.sliver-icon {
  background-color: #f6ffed;
  color: #52c41a;
}

.status-icon {
  background-color: #fff7e6;
  color: #fa8c16;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.status-text.normal {
  color: #67c23a;
}

.status-text.abnormal {
  color: #f56c6c;
}

/* 内容区域 */
.content-row {
  display: flex;
  gap: 20px;
}

.log-card,
.link-card {
  flex: 1;
  border-radius: 16px;
}

.log-card :deep(.el-card__header),
.link-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

/* 日志样式 */
.log-card :deep(.el-timeline) {
  padding: 0;
}

.log-card :deep(.el-timeline-item__content) {
  color: #606266;
}

.log-card :deep(.el-timeline-item__timestamp) {
  color: #909399;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px;
}

/* 工具链接样式 */
.link-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.link-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.link-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.link-name {
  font-size: 14px;
  color: #303133;
}

.link-status {
  font-size: 14px;
  color: #909399;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.connected {
  background-color: #67c23a;
}

.status-dot.disconnected {
  background-color: #f56c6c;
}
</style>