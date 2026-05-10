<template>
  <div class="msf-tool">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>MSF工具</h2>
      <el-button type="primary" @click="openNewAttackDialog">
        <el-icon><Plus /></el-icon>
        新建攻击
      </el-button>
    </div>

    <!-- 攻击任务列表 -->
    <el-card class="task-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>攻击任务列表</span>
          <span class="task-count">({{ tasks.length }}个)</span>
        </div>
      </template>
      <el-table :data="tasks" style="width: 100%">
        <el-table-column prop="id" label="任务ID" width="100" />
        <el-table-column prop="module" label="模块名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sessionId" label="会话ID" width="100">
          <template #default="{ row }">
            {{ row.sessionId || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">
              查看详情
            </el-button>
            <el-button type="danger" link size="small" @click="deleteTask(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建攻击弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建攻击"
      width="700px"
      :close-on-click-modal="false"
      @close="resetDialog"
    >
      <!-- 步骤指示器 -->
      <el-steps :active="activeStep" finish-status="success" class="steps-container">
        <el-step title="选择模块" />
        <el-step title="选择Payload" />
        <el-step title="配置参数" />
      </el-steps>

      <div class="dialog-content">
        <!-- 步骤1: 选择模块 -->
        <div v-show="activeStep === 0" class="step-content">
          <el-form label-width="120px">
            <el-form-item label="模块类型">
              <el-select v-model="moduleType" @change="handleTypeChange" style="width: 100%">
                <el-option label="Exploit" value="exploit" />
                <el-option label="Auxiliary" value="auxiliary" />
                <el-option label="Payload" value="payload" />
                <el-option label="Post" value="post" />
              </el-select>
            </el-form-item>
            <el-form-item label="模块名称">
              <el-select
                v-model="selectedModuleName"
                filterable
                remote
                reserve-keyword
                placeholder="输入关键词搜索模块"
                :remote-method="searchModules"
                :loading="moduleLoading"
                style="width: 100%"
                @change="handleModuleChange"
              >
                <el-option
                  v-for="item in moduleOptions"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
                >
                  <div class="module-option">
                    <span class="module-name">{{ item.name }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤2: 选择Payload -->
        <div v-show="activeStep === 1" class="step-content">
          <div v-if="compatiblePayloads.length > 0">
            <el-form label-width="120px">
              <el-form-item label="Payload">
                <el-select
                  v-model="selectedPayload"
                  filterable
                  placeholder="选择Payload（可选）"
                  style="width: 100%"
                  clearable
                  @change="handlePayloadChange"
                >
                  <el-option
                    v-for="p in compatiblePayloads"
                    :key="p"
                    :label="p"
                    :value="p"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
          <div v-else class="no-payload-tip">
            该模块没有兼容的Payload，将使用默认配置
          </div>
        </div>

        <!-- 步骤3: 配置参数 -->
        <div v-show="activeStep === 2" class="step-content">
          <!-- 基本参数 -->
          <el-form
            ref="formRef"
            label-width="120px"
            :model="formOptions"
            :rules="formRules"
            v-if="basicOptions.length > 0"
          >
            <el-form-item
              v-for="opt in basicOptions"
              :key="opt.name"
              :label="opt.name"
              :prop="opt.name"
            >
              <!-- 布尔类型 -->
              <el-switch
                v-if="opt.type === 'boolean'"
                v-model="formOptions[opt.name]"
              />
              <!-- 整数类型 -->
              <el-input-number
                v-else-if="opt.type === 'integer'"
                v-model="formOptions[opt.name]"
                :min="0"
                :max="65535"
                controls-position="right"
                style="width: 100%"
              />
              <!-- 字符串类型 -->
              <el-input
                v-else
                v-model="formOptions[opt.name]"
                :placeholder="opt.description || opt.name"
              />
            </el-form-item>
          </el-form>

          <!-- 高级参数折叠面板 -->
          <el-collapse v-if="advancedOptions.length > 0" class="advanced-collapse">
            <el-collapse-item title="高级参数" name="advanced">
              <el-form label-width="120px">
                <el-form-item
                  v-for="opt in advancedOptions"
                  :key="opt.name"
                  :label="opt.name"
                >
                  <!-- 布尔类型 -->
                  <el-switch
                    v-if="opt.type === 'boolean'"
                    v-model="formOptions[opt.name]"
                  />
                  <!-- 整数类型 -->
                  <el-input-number
                    v-else-if="opt.type === 'integer'"
                    v-model="formOptions[opt.name]"
                    :min="0"
                    :max="65535"
                    controls-position="right"
                    style="width: 100%"
                  />
                  <!-- 字符串类型 -->
                  <el-input
                    v-else
                    v-model="formOptions[opt.name]"
                    :placeholder="opt.description || opt.name"
                  />
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>

          <div v-if="basicOptions.length === 0 && advancedOptions.length === 0" class="no-options-tip">
            该模块无需配置参数
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="handleCancel">取消</el-button>
        <el-button v-if="activeStep > 0" @click="prevStep">上一步</el-button>
        <el-button
          v-if="activeStep < 2"
          type="primary"
          :disabled="!canGoNext"
          @click="nextStep"
        >
          下一步
        </el-button>
        <el-button
          v-if="activeStep === 2"
          type="primary"
          :loading="attacking"
          :disabled="!canStartAttack"
          @click="startAttack"
        >
          {{ attacking ? '攻击中...' : '开始攻击' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="任务详情" width="500px">
      <el-descriptions :column="1" border v-if="currentTask">
        <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ currentTask.module }}</el-descriptions-item>
        <el-descriptions-item label="Payload">{{ currentTask.payload || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTask.status)" size="small">
            {{ currentTask.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会话ID">{{ currentTask.sessionId || '-' }}</el-descriptions-item>
        <el-descriptions-item label="参数">{{ currentTask.paramsStr || '暂无详情' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentTask.createTime }}</el-descriptions-item>
        <el-descriptions-item label="输出">{{ currentTask.output || '暂无输出' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getModules, getCompatiblePayloads, getModuleOptions, executeExploit, getSessions } from '../api'

// 攻击任务列表（前端内存存储）
const tasks = ref([])

// 步骤
const activeStep = ref(0)

// 模块类型
const moduleType = ref('exploit')

// 模块搜索
const moduleLoading = ref(false)
const moduleOptions = ref([])
const selectedModuleName = ref('')

// 计算属性：根据类型和短名称拼接完整模块路径
const fullModuleName = computed(() => {
  if (!selectedModuleName.value) return ''
  return `${moduleType.value}/${selectedModuleName.value}`
})

// Payload
const compatiblePayloads = ref([])
const selectedPayload = ref('')

// 模块选项
const moduleOptionsList = ref([])
const basicOptions = ref([])
const advancedOptions = ref([])

// 表单参数
const formOptions = ref({})
const formRef = ref(null)
const formRules = ref({})

// 常用参数列表
const commonParams = ['RHOSTS', 'RHOST', 'RPORT', 'LHOST', 'LPORT', 'PAYLOAD', 'SESSION', 'TARGET', 'CMD', 'PATH']

// 分类参数函数
const splitOptions = (options) => {
  // 基本参数：必填参数 + 常用参数
  basicOptions.value = options.filter(opt => opt.required || commonParams.includes(opt.name))
  // 高级参数：非必填且不在常用列表中的参数
  advancedOptions.value = options.filter(opt => !opt.required && !commonParams.includes(opt.name))

  // 生成表单校验规则（仅基本参数中的必填项）
  const rules = {}
  basicOptions.value.forEach(opt => {
    if (opt.required) {
      rules[opt.name] = [{ required: true, message: `请输入${opt.name}`, trigger: 'blur' }]
    }
  })
  formRules.value = rules
}

// 弹窗状态
const dialogVisible = ref(false)
const detailVisible = ref(false)
const attacking = ref(false)
const currentTask = ref(null)

// 轮询定时器管理
const pollingIntervals = {}

// 轮询配置
const POLLING_INTERVAL = 5000 // 5秒
const POLLING_TIMEOUT = 600000 // 10分钟

// 任务ID计数器
let taskIdCounter = 1

// 计算是否可以进入下一步
const canGoNext = computed(() => {
  if (activeStep.value === 0) {
    return selectedModuleName.value !== ''
  }
  if (activeStep.value === 1) {
    // 如果有 payloads 列表，必须选择；否则可以跳过
    return compatiblePayloads.value.length === 0 || selectedPayload.value !== ''
  }
  return false
})

// 计算是否可以开始攻击
const canStartAttack = computed(() => {
  if (!fullModuleName.value) return false

  // 检查必填参数
  const missingParams = moduleOptionsList.value
    .filter(opt => opt.required && (formOptions.value[opt.name] === undefined || formOptions.value[opt.name] === ''))
    .map(opt => opt.name)

  return missingParams.length === 0
})

// 获取状态标签类型
const getStatusType = (status) => {
  const map = {
    '等待执行': 'info',
    '执行中': 'warning',
    '监听中': 'warning',
    '成功': 'success',
    '失败': 'danger'
  }
  return map[status] || 'info'
}

// 启动任务轮询（监听器类型模块）
const startTaskPolling = (task) => {
  // 如果已有定时器，先清除
  if (pollingIntervals[task.id]) {
    clearInterval(pollingIntervals[task.id])
  }

  const interval = setInterval(async () => {
    try {
      // 获取当前所有 MSF 会话
      const res = await getSessions()
      const sessions = res.sessions || []

      // 匹配会话：监听任务的 LPORT 与会话的本地端口或目标端口匹配
      const matchedSession = sessions.find(s => {
        const targetPort = String(task.options.LPORT)
        // 匹配本地端口或目标端口
        return s.local_port === targetPort || s.port === targetPort
      })

      if (matchedSession) {
        // 匹配成功，更新任务状态
        task.status = '成功'
        task.sessionId = matchedSession.id
        task.output = `会话已建立: ${matchedSession.id} (${matchedSession.host})`
        clearInterval(pollingIntervals[task.id])
        delete pollingIntervals[task.id]
        ElMessage.success(`任务 ${task.id} 已建立会话: ${matchedSession.id}`)
        return
      }

      // 检查超时
      if (Date.now() - task.createdAt > POLLING_TIMEOUT) {
        task.status = '失败'
        task.output = '等待超时，未收到连接'
        clearInterval(pollingIntervals[task.id])
        delete pollingIntervals[task.id]
        ElMessage.warning(`任务 ${task.id} 等待超时`)
      }
    } catch (error) {
      console.error('轮询获取会话失败:', error)
    }
  }, POLLING_INTERVAL)

  // 存储定时器ID
  pollingIntervals[task.id] = interval
}

// 停止任务轮询
const stopTaskPolling = (taskId) => {
  if (pollingIntervals[taskId]) {
    clearInterval(pollingIntervals[taskId])
    delete pollingIntervals[taskId]
  }
}

// 停止所有轮询
const stopAllPolling = () => {
  Object.keys(pollingIntervals).forEach(taskId => {
    clearInterval(pollingIntervals[taskId])
  })
  Object.keys(pollingIntervals).forEach(key => delete pollingIntervals[key])
}

// 搜索模块
const searchModules = async (keyword) => {
  if (!keyword) {
    moduleOptions.value = []
    return
  }

  moduleLoading.value = true
  try {
    const res = await getModules(moduleType.value, keyword)
    moduleOptions.value = res.modules || []
  } catch (error) {
    console.error('搜索模块失败:', error)
    ElMessage.error('搜索模块失败')
    moduleOptions.value = []
  } finally {
    moduleLoading.value = false
  }
}

// 模块类型变化
const handleTypeChange = () => {
  selectedModuleName.value = ''
  moduleOptions.value = []
  compatiblePayloads.value = []
  selectedPayload.value = ''
  moduleOptionsList.value = []
  formOptions.value = {}
}

// 模块选择变化
const handleModuleChange = async () => {
  if (!selectedModuleName.value) {
    compatiblePayloads.value = []
    moduleOptionsList.value = []
    formOptions.value = {}
    return
  }

  // 清空之前的选择
  selectedPayload.value = ''
  compatiblePayloads.value = []
  moduleOptionsList.value = []
  formOptions.value = {}

  // 获取兼容 payloads，使用拼接后的完整模块名
  try {
    const payloadRes = await getCompatiblePayloads(fullModuleName.value)
    compatiblePayloads.value = payloadRes.payloads || []
  } catch (error) {
    console.error('获取 payloads 失败:', error)
    compatiblePayloads.value = []
  }

  // 获取模块选项
  await loadModuleOptions()
}

// Payload 选择变化
const handlePayloadChange = async () => {
  await loadModuleOptions()
}

// 加载模块选项
const loadModuleOptions = async () => {
  try {
    const optionsRes = await getModuleOptions(
      fullModuleName.value,
      selectedPayload.value || null
    )
    // 后端直接返回数组，不需要 .options
    moduleOptionsList.value = Array.isArray(optionsRes) ? optionsRes : []

    // 分类参数为基本参数和高级参数
    splitOptions(moduleOptionsList.value)

    // 初始化表单参数
    const newFormOptions = {}
    moduleOptionsList.value.forEach(opt => {
      newFormOptions[opt.name] = opt.default !== undefined ? opt.default : ''
    })
    formOptions.value = newFormOptions
  } catch (error) {
    console.error('获取模块选项失败:', error)
    moduleOptionsList.value = []
    basicOptions.value = []
    advancedOptions.value = []
    formOptions.value = {}
  }
}

// 下一步
const nextStep = () => {
  if (activeStep.value < 2) {
    activeStep.value++
  }
}

// 上一步
const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

// 取消
const handleCancel = () => {
  dialogVisible.value = false
}

// 重置弹窗
const resetDialog = () => {
  activeStep.value = 0
  selectedModuleName.value = ''
  selectedPayload.value = ''
  compatiblePayloads.value = []
  moduleOptionsList.value = []
  basicOptions.value = []
  advancedOptions.value = []
  moduleOptions.value = []
  formOptions.value = {}
  formRules.value = {}
}

// 打开新建攻击弹窗
const openNewAttackDialog = () => {
  activeStep.value = 0
  selectedModuleName.value = ''
  selectedPayload.value = ''
  compatiblePayloads.value = []
  moduleOptionsList.value = []
  basicOptions.value = []
  advancedOptions.value = []
  moduleOptions.value = []
  formOptions.value = {}
  formRules.value = {}
  dialogVisible.value = true
}

// 开始攻击
const startAttack = async () => {
  if (!fullModuleName.value) {
    ElMessage.warning('请选择模块')
    return
  }

  // 检查必填参数
  const missingParams = moduleOptionsList.value
    .filter(opt => opt.required && (formOptions.value[opt.name] === undefined || formOptions.value[opt.name] === ''))
    .map(opt => opt.name)

  if (missingParams.length > 0) {
    ElMessage.warning(`请填写必填参数: ${missingParams.join(', ')}`)
    return
  }

  attacking.value = true

  // 构建请求参数，确保格式符合后端期望
  const requestData = {
    module: fullModuleName.value,
    options: {}
  }

  // 将 options 中的值转换为字符串（MSF RPC 需要字符串类型）
  Object.entries(formOptions.value).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) {
      requestData.options[key] = String(value)
    }
  })

  // 仅当用户选择了 payload 时才添加 payload 字段
  if (selectedPayload.value) {
    requestData.payload = selectedPayload.value
  }

  // 调试日志
  console.log('发送攻击请求:', requestData)

  // 生成新任务
  const newTask = {
    id: `T${taskIdCounter++}`,
    module: fullModuleName.value,
    payload: selectedPayload.value || '',
    status: '执行中',
    sessionId: '',
    createdAt: Date.now(), // 时间戳，用于超时判断
    createTime: new Date().toLocaleString('zh-CN'),
    options: { ...requestData.options }, // 存储监听参数
    paramsStr: Object.entries(formOptions.value)
      .filter(([_, v]) => v !== '' && v !== null && v !== undefined)
      .map(([k, v]) => `${k}=${v}`)
      .join(', '),
    output: ''
  }
  tasks.value.unshift(newTask)

  try {
    const res = await executeExploit(requestData)

    // 更新任务状态
    const taskIndex = tasks.value.findIndex(t => t.id === newTask.id)
    if (taskIndex !== -1) {
      // 执行成功后，如果是监听器类型（multi/handler），状态设为"监听中"并启动轮询
      if (fullModuleName.value.includes('multi/handler') || fullModuleName.value.includes('handler')) {
        tasks.value[taskIndex].status = '监听中'
        startTaskPolling(tasks.value[taskIndex])
      } else if (res.success) {
        tasks.value[taskIndex].status = '成功'
        tasks.value[taskIndex].sessionId = res.session_id || ''
        tasks.value[taskIndex].output = res.output || ''
      } else {
        tasks.value[taskIndex].status = '失败'
        tasks.value[taskIndex].output = res.error || res.message || ''
      }
    }

    ElMessage.success(res.success ? '攻击成功' : '攻击失败')
  } catch (error) {
    const taskIndex = tasks.value.findIndex(t => t.id === newTask.id)
    if (taskIndex !== -1) {
      tasks.value[taskIndex].status = '失败'
      tasks.value[taskIndex].output = error.message || '执行失败'
    }
    ElMessage.error(error.response?.data?.detail || '攻击执行失败')
  } finally {
    attacking.value = false
    dialogVisible.value = false
  }
}

// 查看详情
const viewDetail = (task) => {
  currentTask.value = task
  detailVisible.value = true
}

// 删除任务
const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 [${task.id}] 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index !== -1) {
      // 停止该任务的轮询
      stopTaskPolling(task.id)
      tasks.value.splice(index, 1)
      ElMessage.success('删除成功')
    }
  } catch {
    // 取消删除
  }
}

// 组件卸载时停止所有轮询
onUnmounted(() => {
  stopAllPolling()
})
</script>

<style scoped>
.msf-tool {
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

.task-card {
  border-radius: 16px;
}

.task-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-count {
  color: #909399;
  font-size: 14px;
}

/* 步骤条 */
.steps-container {
  padding: 20px 40px;
  margin-bottom: 20px;
}

/* 弹窗内容 */
.dialog-content {
  min-height: 300px;
}

.step-content {
  padding: 20px;
}

.module-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.module-name {
  font-size: 13px;
  font-weight: 500;
}

.module-fullname {
  font-size: 11px;
  color: #909399;
}

.no-payload-tip,
.no-options-tip {
  text-align: center;
  color: #909399;
  padding: 40px;
}

/* 高级参数折叠面板 */
.advanced-collapse {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.advanced-collapse :deep(.el-collapse-item__header) {
  padding: 0 16px;
  font-weight: 500;
}

.advanced-collapse :deep(.el-collapse-item__content) {
  padding: 16px;
}
</style>