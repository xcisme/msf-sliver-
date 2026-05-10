<template>
  <div class="cross-tool">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>跨工具协同</h2>
    </div>

    <!-- 配置区域 -->
    <el-card class="config-card" shadow="hover">
      <template #header>
        <span>协同配置</span>
      </template>
      <div class="config-content">
        <div class="config-item">
          <div class="config-info">
            <div class="config-label">自动推送</div>
            <div class="config-desc">开启后，MSF获取的新会话自动推送到Sliver</div>
          </div>
          <el-switch
            v-model="autoPush"
            @change="handleAutoPushChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 手动植入区域 -->
    <el-card class="implant-card" shadow="hover">
      <template #header>
        <span>手动植入</span>
      </template>
      <div class="implant-content">
        <div class="implant-form">
          <el-select
            v-model="selectedSession"
            placeholder="选择MSF会话"
            style="width: 300px"
          >
            <el-option
              v-for="session in msfSessions"
              :key="session.id"
              :label="`${session.id} - ${session.host}`"
              :value="session.id"
            />
          </el-select>
          <el-button
            type="primary"
            :disabled="!selectedSession"
            @click="implantToSliver"
          >
            植入 Sliver
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 会话映射表 -->
    <el-card class="mapping-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>会话映射表</span>
          <span class="mapping-count">({{ mappings.length }}条)</span>
        </div>
      </template>
      <el-table :data="mappings" style="width: 100%" v-loading="loading">
        <el-table-column prop="msfSessionId" label="MSF会话ID" width="150" />
        <el-table-column prop="sliverSessionId" label="Sliver会话ID" width="150">
          <template #default="{ row }">
            {{ row.sliverSessionId || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="implantTime" label="植入时间" width="180" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :disabled="row.status === '已连接'"
              @click="reconnect(row)"
            >
              重连
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="deleteMapping(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAutoPush,
  setAutoPush,
  getMsfSessionsForManual,
  manualImplant,
  getMappings,
  deleteMapping as deleteMappingApi,
  reconnectMapping as reconnectMappingApi
} from '../api'

// 自动推送开关
const autoPush = ref(false)

// MSF会话列表
const msfSessions = ref([])

// 选中的MSF会话
const selectedSession = ref('')

// 会话映射表
const mappings = ref([])

// 加载状态
const loading = ref(false)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 获取自动推送状态
    const autoPushRes = await getAutoPush()
    autoPush.value = autoPushRes.enabled

    // 获取MSF会话列表
    const sessionsRes = await getMsfSessionsForManual()
    msfSessions.value = sessionsRes.sessions || []

    // 获取映射列表
    const mappingsRes = await getMappings()
    mappings.value = mappingsRes.mappings || []
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

// 获取状态标签类型
const getStatusType = (status) => {
  const map = {
    '已连接': 'success',
    '连接中': 'warning',
    '已断开': 'danger'
  }
  return map[status] || 'info'
}

// 自动推送开关变化
const handleAutoPushChange = async (value) => {
  try {
    await setAutoPush(value)
    ElMessage.success(value ? '自动推送已开启' : '自动推送已关闭')
  } catch (error) {
    console.error('设置自动推送失败:', error)
    ElMessage.error('设置失败')
  }
}

// 植入到Sliver
const implantToSliver = async () => {
  if (!selectedSession.value) {
    ElMessage.warning('请选择MSF会话')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要将会话 ${selectedSession.value} 植入到 Sliver 吗？`,
      '确认植入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    // 调用接口植入
    ElMessage.info('正在植入中...')

    await manualImplant(selectedSession.value)

    // 刷新映射列表
    const mappingsRes = await getMappings()
    mappings.value = mappingsRes.mappings || []

    ElMessage.success('植入成功')
    selectedSession.value = ''
  } catch {
    // 取消操作
  }
}

// 重连
const reconnect = async (mapping) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新连接映射 [${mapping.msfSessionId}] 吗？`,
      '确认重连',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    ElMessage.info('正在重连...')

    await reconnectMappingApi(mapping.id)

    // 刷新映射列表
    const mappingsRes = await getMappings()
    mappings.value = mappingsRes.mappings || []

    ElMessage.success('重连成功')
  } catch {
    // 取消操作
  }
}

// 删除映射
const deleteMapping = async (mapping) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除映射 [${mapping.msfSessionId}] 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteMappingApi(mapping.id)

    // 刷新映射列表
    const mappingsRes = await getMappings()
    mappings.value = mappingsRes.mappings || []

    ElMessage.success('删除成功')
  } catch {
    // 取消操作
  }
}
</script>

<style scoped>
.cross-tool {
  width: 100%;
  height: 100%;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

/* 配置卡片 */
.config-card,
.implant-card,
.mapping-card {
  border-radius: 16px;
  margin-bottom: 20px;
}

.config-card :deep(.el-card__header),
.implant-card :deep(.el-card__header),
.mapping-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

/* 配置内容 */
.config-content {
  padding: 0 8px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-label {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.config-desc {
  font-size: 13px;
  color: #909399;
}

/* 手动植入 */
.implant-content {
  padding: 0 8px;
}

.implant-form {
  display: flex;
  gap: 16px;
  align-items: center;
}

/* 映射表头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mapping-count {
  color: #909399;
  font-size: 14px;
}
</style>
