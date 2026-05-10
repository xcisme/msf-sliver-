<template>
  <div class="advanced-tool">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>高级工具</h2>
    </div>

    <!-- 内容区域 -->
    <div class="tool-content">
      <!-- IP池管理 -->
      <el-card class="tool-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>IP池管理</span>
            <el-button type="primary" size="small" @click="openAddIpDialog">
              <el-icon><Plus /></el-icon>
              添加IP
            </el-button>
          </div>
        </template>
        <el-table :data="ipPoolList" style="width: 100%" v-loading="ipLoading">
          <el-table-column prop="ip_address" label="IP地址" width="180" />
          <el-table-column prop="description" label="描述" min-width="150">
            <template #default="{ row }">
              {{ row.description || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" link size="small" @click="handleDeleteIp(row.id)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="ip-actions">
          <el-button type="primary" @click="handleTestRandomIp">
            随机测试
          </el-button>
        </div>
      </el-card>

      <!-- 域名动态解析 -->
      <el-card class="tool-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>域名动态解析</span>
          </div>
        </template>
        <div class="card-body">
          <el-form label-width="100px">
            <el-form-item label="域名">
              <el-input v-model="dnsConfig.domain" placeholder="example.com" />
            </el-form-item>
            <el-form-item label="当前解析IP">
              <div class="current-ip">{{ dnsConfig.current_ip }}</div>
            </el-form-item>
            <el-form-item label="更新间隔">
              <el-input-number
                v-model="dnsConfig.update_interval"
                :min="1"
                :max="60"
                controls-position="right"
              />
              <span class="form-unit">分钟</span>
            </el-form-item>
            <el-form-item label="启用">
              <el-switch v-model="dnsConfig.enabled" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveDnsConfig">保存配置</el-button>
              <el-button type="success" @click="handleManualUpdateDns">手动更新</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <!-- 流量混淆设置 -->
      <el-card class="tool-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>流量混淆设置</span>
          </div>
        </template>
        <div class="card-body">
          <el-form label-width="120px">
            <el-form-item label="加密方式">
              <el-select v-model="trafficConfig.encryption" placeholder="选择加密方式" style="width: 200px">
                <el-option label="AES-256-CBC" value="aes-256-cbc" />
                <el-option label="AES-128-CBC" value="aes-128-cbc" />
                <el-option label="RC4" value="rc4" />
                <el-option label="XOR" value="xor" />
                <el-option label="不加密" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item label="随机请求头">
              <el-switch v-model="trafficConfig.random_headers" />
              <span class="form-hint">在HTTP请求中添加随机User-Agent等</span>
            </el-form-item>
            <el-form-item label="数据分片">
              <el-switch v-model="trafficConfig.data_chunking" />
              <span class="form-hint">将数据分片传输以躲避检测</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveTrafficConfig">保存配置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
    </div>

    <!-- 添加IP弹窗 -->
    <el-dialog v-model="addIpDialogVisible" title="添加IP" width="400px">
      <el-form>
        <el-form-item label="IP地址">
          <el-input v-model="newIp" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newIpDesc" placeholder="可选描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addIpDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddIp">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getIpPool,
  addIp,
  deleteIp,
  testRandomIp,
  getDomainDnsConfig,
  updateDomainDnsConfig,
  manualUpdateDns,
  getTrafficConfig,
  updateTrafficConfig
} from '../api'

// IP池列表
const ipPoolList = ref([])
const ipLoading = ref(false)

// 添加IP弹窗
const addIpDialogVisible = ref(false)
const newIp = ref('')
const newIpDesc = ref('')

// 域名解析配置
const dnsConfig = ref({
  domain: '',
  current_ip: '',
  update_interval: 5,
  enabled: false
})

// 流量混淆配置
const trafficConfig = ref({
  encryption: 'aes-256-cbc',
  random_headers: true,
  data_chunking: false
})

// 加载IP池
const fetchIpPool = async () => {
  ipLoading.value = true
  try {
    const res = await getIpPool()
    console.log('IP Pool response:', res)
    // 后端返回 { items: [...], total: N }
    ipPoolList.value = res.items || res.data?.items || []
    console.log('IP Pool list:', ipPoolList.value)
  } catch (error) {
    console.error('加载IP池失败:', error)
    ElMessage.error('加载IP池失败')
    ipPoolList.value = []
  } finally {
    ipLoading.value = false
  }
}

// 加载域名配置
const fetchDnsConfig = async () => {
  try {
    const res = await getDomainDnsConfig()
    dnsConfig.value = {
      domain: res.domain || res.data?.domain || '',
      current_ip: res.current_ip || res.data?.current_ip || '',
      update_interval: res.update_interval || res.data?.update_interval || 5,
      enabled: res.enabled || res.data?.enabled || false
    }
  } catch (error) {
    console.error('加载域名配置失败:', error)
  }
}

// 加载流量配置
const fetchTrafficConfig = async () => {
  try {
    const res = await getTrafficConfig()
    trafficConfig.value = {
      encryption: res.encryption || res.data?.encryption || 'aes-256-cbc',
      random_headers: res.random_headers || res.data?.random_headers || false,
      data_chunking: res.data_chunking || res.data?.data_chunking || false
    }
  } catch (error) {
    console.error('加载流量配置失败:', error)
  }
}

onMounted(() => {
  fetchIpPool()
  fetchDnsConfig()
  fetchTrafficConfig()
})

// 打开添加IP弹窗
const openAddIpDialog = () => {
  newIp.value = ''
  newIpDesc.value = ''
  addIpDialogVisible.value = true
}

// 添加IP
const handleAddIp = async () => {
  if (!newIp.value) {
    ElMessage.warning('请输入IP地址')
    return
  }

  // 简单验证IP格式
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/
  if (!ipRegex.test(newIp.value)) {
    ElMessage.warning('请输入正确的IP地址格式')
    return
  }

  try {
    await addIp(newIp.value, newIpDesc.value)
    await fetchIpPool()
    addIpDialogVisible.value = false
    ElMessage.success('IP添加成功')
  } catch (error) {
    console.error('添加IP失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

// 删除IP
const handleDeleteIp = async (id) => {
  try {
    await deleteIp(id)
    await fetchIpPool()
    ElMessage.success('IP删除成功')
  } catch (error) {
    console.error('删除IP失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

// 随机测试
const handleTestRandomIp = async () => {
  if (ipPoolList.value.length === 0) {
    ElMessage.warning('IP池为空，请先添加IP')
    return
  }

  try {
    const res = await testRandomIp()
    console.log('Random IP response:', res)
    // 后端返回 { selected_ip, message }
    const randomIp = res.selected_ip || res.data?.selected_ip
    if (randomIp) {
      ElMessage.success(`随机IP: ${randomIp}`)
    } else {
      ElMessage.warning('IP池为空或无可用IP')
    }
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('随机测试失败')
  }
}

// 保存域名配置
const handleSaveDnsConfig = async () => {
  try {
    await updateDomainDnsConfig(dnsConfig.value)
    ElMessage.success('域名配置保存成功')
  } catch (error) {
    console.error('保存域名配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

// 手动更新DNS
const handleManualUpdateDns = async () => {
  try {
    ElMessage.info('正在更新域名解析...')
    await manualUpdateDns()
    await fetchDnsConfig()
    ElMessage.success('手动更新成功')
  } catch (error) {
    console.error('手动更新DNS失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

// 保存流量配置
const handleSaveTrafficConfig = async () => {
  try {
    await updateTrafficConfig(trafficConfig.value)
    ElMessage.success('流量配置保存成功')
  } catch (error) {
    console.error('保存流量配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}
</script>

<style scoped>
.advanced-tool {
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

.tool-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tool-card {
  border-radius: 16px;
}

.tool-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.card-body {
  padding: 0 8px;
}

/* IP池管理 */
.ip-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

/* 域名解析 */
.current-ip {
  font-size: 16px;
  font-weight: 500;
  color: #3498db;
  padding: 6px 0;
}

.form-unit {
  margin-left: 10px;
  color: #909399;
  font-size: 14px;
}

.form-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}
</style>