import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTemplateVariables, type TemplateVariableInfo } from '@/api/prompt'

export const useVariablesStore = defineStore('variables', () => {
  const variables = ref<TemplateVariableInfo[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  // 获取变量列表
  const fetchVariables = async () => {
    // 如果已经加载过，直接返回缓存的数据
    if (loaded.value && variables.value.length > 0) {
      return variables.value
    }

    // 如果正在加载，等待加载完成
    if (loading.value) {
      return new Promise<TemplateVariableInfo[]>((resolve) => {
        const checkLoaded = () => {
          if (loaded.value) {
            resolve(variables.value)
          } else {
            setTimeout(checkLoaded, 100)
          }
        }
        checkLoaded()
      })
    }

    loading.value = true
    try {
      const response = await getTemplateVariables()
      variables.value = response.variables
      loaded.value = true
      return variables.value
    } catch (error) {
      console.error('获取变量列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 重置状态
  const reset = () => {
    variables.value = []
    loading.value = false
    loaded.value = false
  }

  return {
    variables,
    loading,
    loaded,
    fetchVariables,
    reset
  }
})
