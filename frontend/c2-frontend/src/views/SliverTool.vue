<template>
  <div class="sliver-tool">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>Sliver工具</h2>
      <el-button type="primary" @click="handleGenerateImplant">
        <el-icon><Plus /></el-icon>
        生成Implant
      </el-button>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：会话列表 -->
      <el-card class="session-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>会话列表</span>
            <span class="session-count">({{ sessions.length }}个)</span>
          </div>
        </template>
        <el-table
          :data="sessions"
          style="width: 100%"
          v-loading="loading"
          highlight-current-row
          @row-click="selectSession"
          :row-class-name="getRowClassName"
        >
          <el-table-column prop="id" label="会话ID" width="80" />
          <el-table-column prop="host" label="主机" min-width="120" />
          <el-table-column prop="user" label="用户" width="100" />
          <el-table-column prop="os" label="操作系统" min-width="120" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click.stop="interactSession(row)">
                交互
              </el-button>
              <el-button type="danger" link size="small" @click.stop="handleDeleteSession(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 右侧：命令执行区域 -->
      <el-card class="command-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>命令执行</span>
            <span v-if="currentSession" class="current-session">
              当前会话：{{ currentSession.id }} ({{ currentSession.host }})
            </span>
            <span v-else class="no-session">未选择会话</span>
          </div>
        </template>

        <div class="command-area">
          <!-- 输出区域 -->
          <div class="output-area" ref="outputArea">
            <div v-if="!currentSession" class="no-session-tip">
              请先选择一个会话
            </div>
            <div v-else class="output-content">
              <div
                v-for="(cmd, index) in commandHistory"
                :key="index"
                class="command-line"
              >
                <div class="cmd-input">
                  <span class="prompt">[root@{{ currentSession.host }}]# </span>
                  <span>{{ cmd.command }}</span>
                </div>
                <div class="cmd-output" v-if="cmd.output">{{ cmd.output }}</div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-area">
            <el-input
              v-model="commandInput"
              placeholder="输入命令..."
              :disabled="!currentSession"
              @keyup.enter="sendCommand"
            >
              <template #append>
                <el-button :disabled="!currentSession" @click="sendCommand">
                  发送命令
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 生成Implant弹窗 -->
    <el-dialog v-model="dialogVisible" title="生成Implant" width="500px">
      <el-form :model="implantForm" label-width="100px">
        <el-form-item label="监听地址">
          <el-input v-model="implantForm.lhost" placeholder="192.168.1.10" />
        </el-form-item>
        <el-form-item label="监听端口">
          <el-input-number v-model="implantForm.lport" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
        <el-form-item label="协议">
          <el-select v-model="implantForm.protocol" style="width: 100%">
            <el-option label="TCP" value="tcp" />
            <el-option label="HTTP" value="http" />
            <el-option label="HTTPS" value="https" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台">
          <el-select v-model="implantForm.platform" style="width: 100%">
            <el-option label="Windows" value="windows" />
            <el-option label="Linux" value="linux" />
            <el-option label="macOS" value="macos" />
          </el-select>
        </el-form-item>
        <el-form-item label="格式">
          <el-select v-model="implantForm.format" style="width: 100%">
            <el-option label="EXE" value="exe" />
            <el-option label="DLL" value="dll" />
            <el-option label="Shellcode" value="shellcode" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitGenerate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSliverSessions, sendSliverCommand, deleteSliverSession, generateImplant } from '../api'

// 会话列表
const sessions = ref([])

// 当前选中的会话
const currentSession = ref(null)

// 命令输入
const commandInput = ref('')

// 命令历史
const commandHistory = ref([])

// 输出区域引用
const outputArea = ref(null)

// 生成Implant弹窗
const dialogVisible = ref(false)
const loading = ref(false)

// Implant 表单
const implantForm = ref({
  lhost: '',
  lport: 8443,
  protocol: 'tcp',
  platform: 'windows',
  format: 'exe'
})

// 加载会话列表
const loadSessions = async () => {
  loading.value = true
  try {
    const res = await getSliverSessions()
    sessions.value = Array.isArray(res) ? res : (res.sessions || [])
  } catch (error) {
    console.error('加载会话列表失败:', error)
    ElMessage.error('加载会话列表失败')
  } finally {
    loading.value = false
  }
}

// 打开生成Implant弹窗
const handleGenerateImplant = () => {
  dialogVisible.value = true
}

// 提交生成Implant
const submitGenerate = async () => {
  if (!implantForm.value.lhost) {
    ElMessage.warning('请输入监听地址')
    return
  }

  try {
    ElMessage.info('正在生成Implant...')
    await generateImplant({
      lhost: implantForm.value.lhost,
      lport: implantForm.value.lport,
      protocol: implantForm.value.protocol,
      platform: implantForm.value.platform,
      format: implantForm.value.format
    })
    ElMessage.success('Implant生成成功')
    dialogVisible.value = false
    // 重置表单
    implantForm.value = {
      lhost: '',
      lport: 8443,
      protocol: 'tcp',
      platform: 'windows',
      format: 'exe'
    }
  } catch (error) {
    console.error('生成Implant失败:', error)
    ElMessage.error(error.response?.data?.detail || '生成失败')
  }
}

// 删除会话
const handleDeleteSession = async (session) => {
  try {
    await ElMessageBox.confirm(`确定要删除会话 [${session.id}] 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteSliverSession(session.id)
    ElMessage.success('删除成功')
    loadSessions()
    // 如果删除的是当前会话
    if (currentSession.value && currentSession.value.id === session.id) {
      currentSession.value = null
      commandHistory.value = []
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadSessions()
})

// 选择会话
const selectSession = (session) => {
  currentSession.value = session
}

// 交互会话
const interactSession = (session) => {
  currentSession.value = session
  ElMessage.success(`已切换到会话 ${session.id}`)
}

// 发送命令
const sendCommand = async () => {
  if (!commandInput.value.trim()) return
  if (!currentSession.value) {
    ElMessage.warning('请先选择会话')
    return
  }

  const cmd = commandInput.value.trim()

  try {
    const res = await sendSliverCommand(currentSession.value.id, cmd)
    commandHistory.value.push({
      command: cmd,
      output: res.output || res.data?.output || '命令执行成功'
    })
  } catch (error) {
    commandHistory.value.push({
      command: cmd,
      output: `Error: ${error.response?.data?.detail || error.message}`
    })
  }

  // 清空输入
  commandInput.value = ''

  // 滚动到底部
  setTimeout(() => {
    if (outputArea.value) {
      outputArea.value.scrollTop = outputArea.value.scrollHeight
    }
  }, 10)
}

// 行样式
const getRowClassName = ({ row }) => {
  if (currentSession.value && currentSession.value.id === row.id) {
    return 'current-row'
  }
  return ''
}
</script>

<style scoped>
.sliver-tool {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
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

.main-content {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.session-card {
  width: 500px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
}

.session-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.session-card :deep(.el-card__body) {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.command-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  min-width: 0;
}

.command-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.command-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.session-count {
  color: #909399;
  font-size: 14px;
}

.current-session {
  font-size: 13px;
  color: #3498db;
  margin-left: auto;
}

.no-session {
  font-size: 13px;
  color: #909399;
  margin-left: auto;
}

/* 命令执行区域 */
.command-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.output-area {
  flex: 1;
  background-color: #1e1e1e;
  padding: 16px;
  overflow-y: auto;
  min-height: 200px;
}

.no-session-tip {
  color: #666;
  text-align: center;
  padding-top: 80px;
  font-size: 14px;
}

.output-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.command-line {
  margin-bottom: 12px;
}

.cmd-input {
  color: #4ec9b0;
}

.prompt {
  color: #9cdcfe;
}

.cmd-output {
  color: #d4d4d4;
  margin-top: 4px;
  white-space: pre-wrap;
  word-break: break-all;
}

.input-area {
  padding: 16px;
  background-color: #252525;
  border-top: 1px solid #333;
}

.input-area :deep(.el-input-group__append) {
  background-color: #3498db;
  border-color: #3498db;
  color: #fff;
}

.input-area :deep(.el-input-group__append .el-button) {
  color: #fff;
}

.input-area :deep(.el-input__wrapper) {
  background-color: #2d2d2d;
  box-shadow: none;
  border-color: #3d3d3d;
}

.input-area :deep(.el-input__inner) {
  color: #fff;
}

/* 当前会话行高亮 */
.session-card :deep(.el-table .current-row td) {
  background-color: #ecf5ff !important;
}
</style>
