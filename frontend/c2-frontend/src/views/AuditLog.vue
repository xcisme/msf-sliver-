<template>
  <div class="audit-log">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>审计日志</h2>
      <el-button type="primary" @click="handleExport">
        <el-icon><Download /></el-icon>
        导出CSV
      </el-button>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card" shadow="hover">
      <div class="filter-content">
        <div class="filter-row">
          <div class="filter-item">
            <label>时间范围</label>
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 380px"
            />
          </div>

          <div class="filter-item">
            <label>操作类型</label>
            <el-select v-model="operationType" placeholder="选择操作类型" style="width: 180px" clearable>
              <el-option
                v-for="action in actionOptions"
                :key="action.value"
                :label="action.label"
                :value="action.value"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <label>关键词</label>
            <el-input
              v-model="keyword"
              placeholder="搜索目标/操作"
              style="width: 200px"
              clearable
            />
          </div>

          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><RefreshRight /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="table-card" shadow="hover">
      <el-table :data="logs" style="width: 100%" v-loading="loading">
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="action" label="操作类型" width="130">
          <template #default="{ row }">
            <el-tag :type="getOperationTypeTag(row.action)" size="small">
              {{ getOperationTypeLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="目标" min-width="200" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">
              {{ row.result }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, RefreshRight, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getLogs, getLogActions } from '../api'

// 筛选条件
const dateRange = ref([])
const operationType = ref('')
const keyword = ref('')

// 操作类型选项
const actionOptions = ref([
  { value: 'login', label: '登录' },
  { value: 'exploit', label: '执行Exploit' },
  { value: 'command', label: '执行命令' },
  { value: 'implant', label: '植入会话' },
  { value: 'stop_session', label: '结束会话' },
  { value: 'delete', label: '删除操作' }
])

// 日志数据
const logs = ref([])
const total = ref(0)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 加载状态
const loading = ref(false)

// 加载日志数据
const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      keyword: keyword.value || undefined,
      action: operationType.value || undefined
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0]
      params.end_time = dateRange.value[1]
    }

    const res = await getLogs(params)
    console.log('Logs response:', res)

    // 后端直接返回 { total, items }
    logs.value = res.items || res.data?.items || []
    total.value = res.total || res.data?.total || 0

    console.log('Logs items:', logs.value, 'Total:', total.value)
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 加载操作类型选项（可选）
const fetchActionOptions = async () => {
  try {
    const res = await getLogActions()
    if (res.data && res.data.length > 0) {
      actionOptions.value = res.data
    }
  } catch (error) {
    console.error('获取操作类型失败:', error)
    // 使用默认选项
  }
}

onMounted(() => {
  fetchLogs()
  fetchActionOptions()
})

// 获取操作类型标签
const getOperationTypeTag = (type) => {
  const map = {
    'login': 'primary',
    'exploit': 'warning',
    'command': 'info',
    'implant': 'success',
    'stop_session': 'danger',
    'delete': 'danger'
  }
  return map[type] || 'info'
}

// 获取操作类型标签文本
const getOperationTypeLabel = (type) => {
  const map = {
    'login': '登录',
    'exploit': '执行Exploit',
    'command': '执行命令',
    'implant': '植入会话',
    'stop_session': '结束会话',
    'delete': '删除操作'
  }
  return map[type] || type
}

// 查询
const handleSearch = () => {
  currentPage.value = 1
  fetchLogs()
}

// 重置
const handleReset = () => {
  dateRange.value = []
  operationType.value = ''
  keyword.value = ''
  currentPage.value = 1
  fetchLogs()
  ElMessage.info('已重置筛选条件')
}

// 分页大小变化
const handleSizeChange = () => {
  currentPage.value = 1
  fetchLogs()
}

// 当前页变化
const handleCurrentChange = () => {
  fetchLogs()
}

// 导出CSV
const handleExport = () => {
  if (logs.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  // 表头
  const headers = ['时间', '用户', '操作类型', '目标', '结果']

  // 数据行
  const rows = logs.value.map(log => [
    log.created_at || log.time,
    log.username || log.user,
    getOperationTypeLabel(log.action || log.operationType),
    log.target,
    log.result
  ])

  // 构建CSV内容
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  // 添加BOM以支持中文
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })

  // 创建下载链接
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `审计日志_${new Date().toLocaleString('zh-CN').replace(/[/:]/g, '-')}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success(`导出成功，共 ${logs.value.length} 条记录`)
}
</script>

<style scoped>
.audit-log {
  width: 100%;
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

/* 筛选卡片 */
.filter-card {
  margin-bottom: 20px;
  border-radius: 16px;
}

.filter-card :deep(.el-card__body) {
  padding: 20px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-item label {
  font-size: 14px;
  color: #606266;
}

.filter-actions {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

/* 表格卡片 */
.table-card {
  border-radius: 16px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}
</style>