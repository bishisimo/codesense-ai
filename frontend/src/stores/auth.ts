import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('auth_token') || '')
  const user = ref<any>(null)

  const isAuthenticated = computed(() => !!token.value)

  const login = async (password: string) => {
    try {
      // 验证密码不为空
      if (!password || password.trim() === '') {
        throw new Error('密码不能为空')
      }
      
      const response = await authApi.login(password)
      token.value = response.access_token
      localStorage.setItem('auth_token', token.value)
      
      // 获取用户信息
      const userInfo = await authApi.getUserInfo()
      user.value = userInfo
      
      return true
    } catch (error) {
      console.error('Login failed:', error)
      // 确保登录失败时清除任何可能存在的token
      token.value = ''
      user.value = null
      localStorage.removeItem('auth_token')
      throw error
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      token.value = ''
      user.value = null
      localStorage.removeItem('auth_token')
    }
  }

  const refreshUserInfo = async () => {
    try {
      const userInfo = await authApi.getUserInfo()
      user.value = userInfo
    } catch (error) {
      console.error('Failed to refresh user info:', error)
      logout()
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    refreshUserInfo
  }
})
