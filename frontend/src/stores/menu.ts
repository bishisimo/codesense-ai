import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type MenuConfig } from '@/api/auth'

// 菜单详细信息（前端内置）
const menuDetails = {
  dashboard: {
    name: "仪表板",
    path: "/admin/dashboard",
    icon: "Monitor"
  },
  merge_requests: {
    name: "AI审查",
    path: "/admin/merge-requests",
    icon: "Cpu"
  },
  statistics: {
    name: "数据统计",
    path: "/admin/statistics",
    icon: "TrendCharts"
  },
  prompt_templates: {
    name: "Prompt模板",
    path: "/admin/prompt-templates",
    icon: "Edit"
  }
} as const

export const useMenuStore = defineStore('menu', () => {
  const menuConfig = ref<MenuConfig | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取菜单配置
  const fetchMenuConfig = async () => {
    if (menuConfig.value) {
      return menuConfig.value
    }

    loading.value = true
    error.value = null
    
    try {
      const config = await authApi.getMenuConfig()
      menuConfig.value = config
      return config
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取菜单配置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 计算启用的菜单项
  const enabledMenus = computed(() => {
    if (!menuConfig.value) return []
    
    return Object.entries(menuConfig.value)
      .filter(([key, enabled]) => enabled)
      .map(([key, _]) => ({
        key,
        ...menuDetails[key as keyof typeof menuDetails]
      }))
  })

  // 检查特定菜单是否启用
  const isMenuEnabled = (menuKey: keyof MenuConfig) => {
    return menuConfig.value?.[menuKey] ?? false
  }

  // 获取菜单详细信息
  const getMenuDetails = (menuKey: keyof typeof menuDetails) => {
    return menuDetails[menuKey]
  }

  // 重置状态
  const reset = () => {
    menuConfig.value = null
    loading.value = false
    error.value = null
  }

  return {
    menuConfig,
    loading,
    error,
    enabledMenus,
    fetchMenuConfig,
    isMenuEnabled,
    getMenuDetails,
    reset
  }
})
