import axios, { type AxiosResponse, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { env } from '../../env.config'

// 创建axios实例
const request = axios.create({
  baseURL: env.IS_DEV ? `${env.API_BASE_URL}/api` : '/api',
  timeout: 30000,
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const { response } = error
    
    if (response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
      return Promise.reject(error)
    }
    
    const message = response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    
    return Promise.reject(error)
  }
)

// 创建自定义的request函数，明确返回类型
const customRequest = <T = any>(config: AxiosRequestConfig): Promise<T> => {
  return request(config)
}

export default customRequest
