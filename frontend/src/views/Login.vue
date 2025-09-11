<template>
  <div class="login-container">
    <div class="login-form">
      <h1 class="login-title">GitLab代码审查系统</h1>
      <p class="login-subtitle">请输入管理员密码登录</p>
      
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules" 
        @submit.prevent="handleLogin"
        autocomplete="off"
      >
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入管理员密码"
            size="large"
            show-password
            :disabled="loading"
            autocomplete="new-password"
            name="admin-password"
            @keyup.enter="handleLogin"
            ref="passwordInputRef"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
            native-type="submit"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'

// 定义组件名称
defineOptions({
  name: 'LoginPage'
})
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()
const passwordInputRef = ref<HTMLInputElement>()
const loading = ref(false)

const loginForm = reactive({
  password: ''
})

const loginRules = {
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 1, message: '密码不能为空', trigger: 'blur' }
  ]
}

// 防止浏览器自动填充和增强安全性
onMounted(() => {
  // 清空表单
  loginForm.password = ''
  
  // 禁用浏览器自动填充
  const inputs = document.querySelectorAll('input[type="password"]')
  inputs.forEach(input => {
    input.setAttribute('autocomplete', 'new-password')
    input.setAttribute('data-form-type', 'other')
    input.setAttribute('data-lpignore', 'true')
  })
  
  // 聚焦到密码输入框
  nextTick(() => {
    passwordInputRef.value?.focus()
  })
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    // 验证表单
    await loginFormRef.value.validate()
    
    // 防止重复提交
    if (loading.value) return
    
    loading.value = true
    
    // 登录
    await authStore.login(loginForm.password)
    
    // 清空密码
    loginForm.password = ''
    
    // 使用 replace 而不是 push，避免浏览器后退到登录页
    await router.replace('/admin/dashboard')
    
  } catch (error: any) {
    console.error('Login error:', error)
    
    // 更详细的错误处理
    let errorMessage = '登录失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
    
    // 登录失败后聚焦到密码输入框
    nextTick(() => {
      passwordInputRef.value?.focus()
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-form {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-title {
  text-align: center;
  margin-bottom: 10px;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.login-subtitle {
  text-align: center;
  margin-bottom: 30px;
  color: #909399;
  font-size: 14px;
}
</style>
