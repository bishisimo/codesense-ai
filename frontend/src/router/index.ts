import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/views/Layout.vue'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import MergeRequests from '@/views/MergeRequests.vue'
import ReviewDetail from '@/views/ReviewDetail.vue'
import PromptTemplates from '@/views/PromptTemplates.vue'
import PromptTemplateEdit from '@/views/PromptTemplateEdit.vue'
import UnifiedTemplateCreate from '@/views/UnifiedTemplateCreate.vue'
import Statistics from '@/views/Statistics.vue'
import { useMenuStore } from '@/stores/menu'

// 基础路由配置
const baseRoutes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'Layout',
    component: Layout,
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'admin/dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'admin/merge-requests',
        name: 'MergeRequests',
        component: MergeRequests
      },
      {
        path: 'admin/review/:id',
        name: 'ReviewDetail',
        component: ReviewDetail
      }
    ]
  }
]

// 可选路由配置
const optionalRoutes = [
  {
    path: '/admin/prompt-templates',
    name: 'PromptTemplates',
    component: PromptTemplates
  },
  {
    path: '/admin/prompt-templates/create',
    name: 'PromptTemplateCreate',
    component: UnifiedTemplateCreate
  },
  {
    path: '/admin/prompt-templates/:id/edit',
    name: 'PromptTemplateEdit',
    component: PromptTemplateEdit
  },
  {
    path: '/admin/statistics',
    name: 'Statistics',
    component: Statistics
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: baseRoutes
})

// 动态添加路由的函数
export const addOptionalRoutes = () => {
  const menuStore = useMenuStore()
  
  // 获取当前已注册的路由名称
  const existingRouteNames = router.getRoutes().map(route => route.name)
  
  // 根据菜单配置添加路由
  if (menuStore.isMenuEnabled('prompt_templates')) {
    const promptRoutes = optionalRoutes.filter(route => 
      route.name === 'PromptTemplates' || 
      route.name === 'PromptTemplateCreate' || 
      route.name === 'PromptTemplateEdit'
    )
    
    promptRoutes.forEach(route => {
      if (!existingRouteNames.includes(route.name)) {
        // 将绝对路径转换为相对路径（去掉开头的"/"）
        const relativeRoute = {
          ...route,
          path: route.path.startsWith('/') ? route.path.slice(1) : route.path
        }
        router.addRoute('Layout', relativeRoute)
      }
    })
  }
  
  if (menuStore.isMenuEnabled('statistics')) {
    const statisticsRoute = optionalRoutes.find(route => route.name === 'Statistics')
    if (statisticsRoute && !existingRouteNames.includes(statisticsRoute.name)) {
      // 将绝对路径转换为相对路径（去掉开头的"/"）
      const relativeRoute = {
        ...statisticsRoute,
        path: statisticsRoute.path.startsWith('/') ? statisticsRoute.path.slice(1) : statisticsRoute.path
      }
      router.addRoute('Layout', relativeRoute)
    }
  }
}

export default router
