<template>
  <div class="app-layout">
    <!-- 顶部栏 -->
    <div class="header">
      <div class="header-left">
        <h1 class="title">C2协同工具</h1>
      </div>
      <div class="header-right">
        <span class="header-item">
          <el-icon><Bell /></el-icon>
          通知
        </span>
        <span class="header-item">
          <el-icon><User /></el-icon>
          admin
        </span>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="main-container">
      <!-- 侧边栏 -->
      <div class="sidebar">
        <el-menu
          :default-active="activeIndex"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="1">
            <el-icon><Monitor /></el-icon>
            <span>控制台概览</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon><Aim /></el-icon>
            <span>MSF工具</span>
          </el-menu-item>
          <el-menu-item index="3">
            <el-icon><Connection /></el-icon>
            <span>Sliver工具</span>
          </el-menu-item>
          <el-menu-item index="4">
            <el-icon><Link /></el-icon>
            <span>跨工具协同</span>
          </el-menu-item>
          <el-menu-item index="5">
            <el-icon><Tools /></el-icon>
            <span>高级工具</span>
          </el-menu-item>
          <el-menu-item index="6">
            <el-icon><Document /></el-icon>
            <span>审计日志</span>
          </el-menu-item>
        </el-menu>

        <!-- 底部用户信息 -->
        <div class="sidebar-footer">
          <div class="user-info">
            <el-icon><User /></el-icon>
            <span>admin</span>
          </div>
          <el-button type="primary" link @click="handleLogout">退出</el-button>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="content">
        <component :is="currentComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, User, Monitor, Aim, Connection, Link, Tools, Document } from '@element-plus/icons-vue'
import Dashboard from './Dashboard.vue'
import MsfTool from './MsfTool.vue'
import SliverTool from './SliverTool.vue'
import CrossTool from './CrossTool.vue'
import AdvancedTool from './AdvancedTool.vue'
import AuditLog from './AuditLog.vue'

const router = useRouter()
const activeIndex = ref('1')

// 组件映射
const componentMap = {
  '1': Dashboard,
  '2': MsfTool,
  '3': SliverTool,
  '4': CrossTool,
  '5': AdvancedTool,
  '6': AuditLog
}

const currentComponent = ref(Dashboard)

const handleMenuSelect = (index) => {
  activeIndex.value = index
  currentComponent.value = componentMap[index]
}

// 退出登录
const handleLogout = () => {
  localStorage.removeItem('c2_token')
  ElMessage.success('已退出登录')
  router.push('/')
}
</script>

<style scoped>
.app-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏样式 */
.header {
  height: 60px;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-left .title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
}

.header-item:hover {
  color: #3498db;
}

/* 主体容器 */
.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: 240px;
  background-color: #ffffff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.sidebar-menu :deep(.el-menu-item) {
  color: #606266;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #ecf5ff !important;
  color: #3498db !important;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: #f5f7fa !important;
  color: #3498db;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

/* 主内容区样式 */
.content {
  flex: 1;
  background-color: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
}
</style>
