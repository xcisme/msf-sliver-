<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="title">C2 系统登录</h2>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '../api'

// 表单绑定对象
const form = ref({
  username: '',
  password: ''
})

// 表单校验规则
const rules = ref({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
})

// 表单引用
const formRef = ref(null)

// 加载状态
const loading = ref(false)

// 路由实例
const router = useRouter()

// 登录方法
const handleLogin = async () => {
  // 表单校验
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 开始加载
    loading.value = true

    try {
      // 调用登录接口
      const res = await login(form.value.username, form.value.password)
      // 获取 token（api/index.js 的响应拦截器已处理，直接取 res.access_token）
      const token = res.access_token
      // 存储 token
      localStorage.setItem('c2_token', token)
      // 提示成功
      ElMessage.success('登录成功')
      // 跳转到仪表盘
      router.push('/dashboard')
    } catch (error) {
      const msg = error.response?.data?.detail || error.response?.data?.message || '登录失败，请检查账号密码'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0b1c2f 0%, #1a2d4a 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.login-card {
  background: rgba(30, 43, 60, 0.9);
  border-radius: 20px;
  padding: 40px 30px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
  box-sizing: border-box;
  width: 400px;
}

.title {
  color: #e9ecef;
  font-size: 24px;
  text-align: center;
  margin-bottom: 30px;
  font-weight: 600;
}

.login-form {
  width: 100%;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  background-color: #2c3e50;
  border-color: #2c3e50;
  border-radius: 8px;
  box-shadow: none;
}

.login-form :deep(.el-input__inner) {
  color: #e9ecef;
  height: 44px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #adb5bd;
}

.login-form :deep(.el-input__wrapper:focus-within) {
  border-color: #3498db;
}

.login-form :deep(.el-input__prefix) {
  color: #adb5bd;
}

.login-button {
  width: 100%;
  height: 44px;
  background-color: #3498db;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  color: #ffffff;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.login-button:hover {
  background-color: #2980b9;
}

.login-button:active {
  background-color: #2980b9;
}
</style>
