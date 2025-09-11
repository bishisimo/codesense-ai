<template>
  <div class="page-container">

    
    <div class="main-content">
      <el-aside class="sidebar" :class="{ 'collapsed': isCollapsed }">
        <!-- 折叠按钮 -->
        <div class="sidebar-header">
          <div class="logo-container" @click="handleLogoClick">
            <div class="logo-icon">
              <el-icon v-if="!isCollapsed"><MagicStick /></el-icon>
              <el-icon v-else><ArrowRight /></el-icon>
            </div>
            <div class="logo-text-container">
              <span class="logo-text">CodeSense-AI</span>
            </div>
          </div>
          <el-button 
            @click="toggleSidebar" 
            class="collapse-btn"
            :icon="isCollapsed ? Expand : Fold"
            text
            size="small"
          />
        </div>
        
        <el-menu
          :default-active="activeMenu"
          router
          unique-opened
          class="sidebar-menu"
          :collapse="false"
          background-color="#ffffff"
          text-color="#606266"
          active-text-color="#8b5cf6"
        >
          <el-menu-item 
            v-for="menu in menuStore.enabledMenus" 
            :key="menu.key"
            :index="menu.path" 
            class="menu-item"
          >
            <el-icon>
              <component :is="getIcon(menu.icon)" />
            </el-icon>
            <span class="menu-text">{{ menu.name }}</span>
          </el-menu-item>
        </el-menu>
        
        <!-- 设置区域 -->
        <div class="sidebar-footer">
          <el-dropdown 
            @command="handleCommand"
            trigger="click"
            :hide-on-click="false"
            placement="top-end"
          >
            <div class="settings-button">
              <el-icon><Setting /></el-icon>
              <span class="settings-text">设置</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-aside>
      
      <main class="content" :class="{ 'expanded': isCollapsed }">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// 定义组件名称
defineOptions({
  name: 'LayoutPage'
})
import { ElMessageBox, ElMessage } from 'element-plus'
import { 
  Monitor, 
  DocumentCopy,
  Edit,
  TrendCharts,
  Fold,
  Expand,
  ArrowRight,
  Cpu,
  Setting,
  SwitchButton,
  MagicStick
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useMenuStore } from '@/stores/menu'
import { addOptionalRoutes } from '@/router'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const menuStore = useMenuStore()

// 侧边栏折叠状态
const isCollapsed = ref(false)

const activeMenu = computed(() => route.path)

// 图标映射
const iconMap: Record<string, any> = {
  Monitor,
  Cpu,
  TrendCharts,
  Edit
}

// 获取图标组件
const getIcon = (iconName: string) => {
  return iconMap[iconName] || Monitor
}

// 组件挂载时获取菜单配置
onMounted(async () => {
  try {
    await menuStore.fetchMenuConfig()
    // 根据菜单配置动态添加路由
    addOptionalRoutes()
  } catch (error) {
    console.error('获取菜单配置失败:', error)
  }
})

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  console.log('侧边栏状态:', isCollapsed.value ? '已折叠' : '已展开')
}

// 点击Logo处理
const handleLogoClick = () => {
  // 如果当前是折叠状态，点击Logo则展开
  if (isCollapsed.value) {
    isCollapsed.value = false
    console.log('点击Logo展开侧边栏')
  }
}

// 处理设置菜单命令
const handleCommand = async (command: string) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm(
        '确定要退出登录吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          closeOnClickModal: false,
          closeOnPressEscape: true,
        }
      )
      
      await authStore.logout()
      
      // 使用 replace 避免浏览器后退
      await router.replace('/login')
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Logout error:', error)
        ElMessage.error('退出登录失败，请重试')
      }
    }
  }
}


</script>

<style scoped>
.page-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}



.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 250px;
  background: #ffffff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 999;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

/* 侧边栏头部 */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  flex-shrink: 0;
  min-width: 0;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  min-width: 0;
  flex-shrink: 0;
}

.logo-container:hover {
  background: rgba(139, 92, 246, 0.1);
  transform: scale(1.02);
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.logo-container:hover .logo-icon {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.logo-text-container {
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  width: auto;
  opacity: 1;
}

.sidebar.collapsed .logo-text-container {
  width: 0;
  opacity: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  display: block;
}

.collapse-btn {
  color: #606266;
  font-size: 16px;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s ease;
  background: transparent;
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background-color: #f3f4f6;
  color: #409eff;
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: #ffffff;
  overflow: hidden;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  color: #606266;
  white-space: nowrap;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  color: #8b5cf6;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2);
  transform: translateX(2px);
}

.sidebar-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  border-radius: 0 2px 2px 0;
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  font-size: 16px;
  margin-right: 12px;
  transition: all 0.2s ease;
}

.sidebar-menu :deep(.el-menu-item:hover .el-icon) {
  transform: scale(1.05);
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  transform: scale(1.05);
}

/* 自定义菜单文字动画 */
.menu-text {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 1;
  transform: translateX(0);
  display: inline-block;
}

.sidebar.collapsed .menu-text {
  opacity: 0;
  transform: translateX(-10px);
  width: 0;
  overflow: hidden;
}

/* 设置区域样式 */
.sidebar-footer {
  margin-top: auto;
  padding: 16px 12px;
  border-top: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  flex-shrink: 0;
}

.settings-button {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: #606266;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.settings-button:hover {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.2);
}

.settings-button:active {
  transform: translateY(0);
  background: rgba(139, 92, 246, 0.15);
}

.settings-button .el-icon {
  font-size: 16px;
  transition: all 0.2s ease;
}

.settings-button:hover .el-icon {
  transform: scale(1.1);
}

.settings-text {
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 1;
  transform: translateX(0);
  display: inline-block;
}

.sidebar.collapsed .settings-text {
  opacity: 0;
  transform: translateX(-10px);
  width: 0;
  overflow: hidden;
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f8fafc;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.content.expanded {
  margin-left: 0;
}

/* 优化下拉菜单样式 */
:deep(.el-dropdown-menu) {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid #e4e7ed;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

:deep(.el-dropdown-menu__item) {
  padding: 12px 20px;
  font-size: 14px;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 4px 8px;
}

:deep(.el-dropdown-menu__item:hover) {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  color: #8b5cf6;
  transform: translateX(4px);
}

:deep(.el-dropdown-menu__item.is-disabled) {
  color: #c0c4cc;
  cursor: not-allowed;
}

/* 确保下拉菜单在正确的层级显示 */
:deep(.el-popper) {
  z-index: 3000;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    transform: translateX(-100%);
    z-index: 1001;
  }
  
  .sidebar.collapsed {
    transform: translateX(0);
  }
  
  .content {
    padding: 16px;
  }
}
</style>
