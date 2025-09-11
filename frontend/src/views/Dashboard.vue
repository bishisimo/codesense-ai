<template>
  <div class="dashboard-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">
        <el-icon class="title-icon"><DataBoard /></el-icon>
        系统概览
      </h2>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-section">
      <!-- 统计卡片网格 -->
      <div class="stats-grid">
        <div class="stats-card">
          <div class="stats-icon projects-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ stats.total_projects }}</div>
            <div class="stats-label">总项目数</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon merge-requests-icon">
            <el-icon><DocumentCopy /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ stats.total_merge_requests }}</div>
            <div class="stats-label">总合并请求</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon opened-icon">
            <el-icon><Share /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ stats.opened_merge_requests }}</div>
            <div class="stats-label">打开状态</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon reviewed-icon">
            <el-icon><Check /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ stats.reviewed_merge_requests }}</div>
            <div class="stats-label">已审查</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon pending-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ stats.pending_merge_requests }}</div>
            <div class="stats-label">待审查</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon today-reviews-icon">
            <el-icon><View /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ stats.today_reviews }}</div>
            <div class="stats-label">今日审查</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon tokens-icon">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ formatTokens(stats.total_tokens) }}</div>
            <div class="stats-label">Token使用量</div>
            <div class="stats-subtitle">本月: {{ formatTokens(stats.monthly_tokens) }}</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon cache-tokens-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ formatTokens(stats.total_cache_tokens) }}</div>
            <div class="stats-label">Cache Token</div>
            <div class="stats-subtitle">本月: {{ formatTokens(stats.monthly_cache_tokens) }}</div>
          </div>
        </div>
        
        <div class="stats-card">
          <div class="stats-icon direct-tokens-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stats-content">
            <div class="stats-number">{{ formatTokens(stats.total_direct_tokens) }}</div>
            <div class="stats-label">Direct Token</div>
            <div class="stats-subtitle">本月: {{ formatTokens(stats.monthly_direct_tokens) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快速操作 -->
    <el-card class="actions-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Operation /></el-icon>
            快速操作
          </span>
        </div>
      </template>
      
      <div class="actions-grid">
        <el-card 
          shadow="hover" 
          class="action-card sync-action-card"
          @click="handleSync"
          :class="{ 'syncing': syncing, 'disabled': syncing }"
        >
          <div class="action-content">
            <div class="action-icon">
              <el-icon class="sync-icon" :class="{ 'syncing': syncing }"><Refresh /></el-icon>
            </div>
            <div class="action-text">
              <h3>{{ syncing ? '同步中...' : '同步GitLab数据' }}</h3>
              <p>{{ syncing ? (syncMessage || '正在从GitLab同步数据，请稍候...') : '从GitLab同步最新的项目和合并请求数据' }}</p>
            </div>
            <div class="action-status" v-if="syncing">
              <div class="sync-progress">
                <div class="progress-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
                <span class="progress-text">处理中</span>
              </div>
            </div>
          </div>
        </el-card>
        
        <el-card 
          shadow="hover" 
          class="action-card"
          @click="goToMergeRequests"
        >
          <div class="action-content">
            <div class="action-icon">
              <el-icon><DocumentCopy /></el-icon>
            </div>
            <div class="action-text">
              <h3>管理合并请求</h3>
              <p>查看和管理所有合并请求的代码审查状态</p>
            </div>
          </div>
        </el-card>
        
        <el-card shadow="hover" class="action-card">
          <div class="action-content">
            <div class="action-icon">
              <el-icon><Setting /></el-icon>
            </div>
            <div class="action-text">
              <h3>系统设置</h3>
              <p>配置GitLab连接、AI模型和通知方式</p>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// 定义组件名称
defineOptions({
  name: 'DashboardPage'
})
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  DataBoard, 
  DocumentCopy, 
  Setting, 
  Folder, 
  Check, 
  Clock, 
  Refresh, 
  Operation,
  Loading,
  Cpu,
  View,
  Box,
  Connection
} from '@element-plus/icons-vue'
import { adminApi, type Stats } from '@/api/admin'

const router = useRouter()

const stats = ref<Stats>({
  total_projects: 0,
  total_merge_requests: 0,
  reviewed_merge_requests: 0,
  pending_merge_requests: 0,
  opened_merge_requests: 0,
  total_tokens: 0,
  monthly_tokens: 0,
  total_direct_tokens: 0,
  total_cache_tokens: 0,
  monthly_direct_tokens: 0,
  monthly_cache_tokens: 0,
  today_reviews: 0
})

const syncing = ref(false)
const syncTaskId = ref<string | null>(null)
const syncMessage = ref('')

const formatTokens = (tokens: number): string => {
  if (tokens === 0) return '0'
  if (tokens < 1000) return tokens.toString()
  if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`
  return `${(tokens / 1000000).toFixed(1)}M`
}

const loadStats = async () => {
  try {
    stats.value = await adminApi.getStats()
  } catch (error) {
    ElMessage.error('加载统计信息失败')
  }
}

// 任务状态轮询间隔存储
const taskPollingIntervals = new Map<string, number>()

const handleSync = async () => {
  // 防重复提交检查
  if (syncing.value) {
    ElMessage.warning('同步任务正在进行中，请勿重复提交')
    return
  }

  try {
    syncing.value = true
    syncMessage.value = '正在提交同步任务...'
    
    const result = await adminApi.syncGitLabData()
    
    if (result.success) {
      ElMessage.success('同步任务已提交，正在后台执行')
      syncMessage.value = '同步任务已提交，正在处理...'
      
      // 如果有任务ID，开始轮询任务状态
      if (result.task_id) {
        syncTaskId.value = result.task_id
        pollTaskStatus(result.task_id)
      } else {
        // 没有任务ID，等待一段时间后重置状态
        setTimeout(() => {
          resetSyncState()
        }, 3000)
      }
    } else {
      ElMessage.error(result.message || '提交同步任务失败')
      resetSyncState()
    }
  } catch (error) {
    console.error('同步失败:', error)
    ElMessage.error('同步失败')
    resetSyncState()
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: string) => {
  try {
    const response = await adminApi.getTaskStatus(taskId)
    
    if (response.success) {
      const { status, message, result, error } = response
      
      // 更新消息
      if (message) {
        syncMessage.value = message
      }
      
      // 任务完成处理
      if (status === 'completed') {
        ElMessage.success('同步任务完成')
        clearTaskPolling(taskId)
        resetSyncState()
        // 刷新统计数据
        await loadStats()
      } else if (status === 'failed') {
        ElMessage.error(`同步任务失败: ${error || message}`)
        clearTaskPolling(taskId)
        resetSyncState()
      } else if (status === 'cancelled') {
        ElMessage.warning('同步任务已取消')
        clearTaskPolling(taskId)
        resetSyncState()
      } else if (status === 'running' || status === 'pending') {
        // 继续轮询
        const intervalId = setTimeout(() => {
          pollTaskStatus(taskId)
        }, 2000) // 每2秒轮询一次
        taskPollingIntervals.set(taskId, intervalId)
      }
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
    ElMessage.error('获取任务状态失败')
    clearTaskPolling(taskId)
    resetSyncState()
  }
}

// 清除任务轮询
const clearTaskPolling = (taskId: string) => {
  const intervalId = taskPollingIntervals.get(taskId)
  if (intervalId) {
    clearTimeout(intervalId)
    taskPollingIntervals.delete(taskId)
  }
}

// 重置同步状态
const resetSyncState = () => {
  syncing.value = false
  syncTaskId.value = null
  syncMessage.value = ''
}

const goToMergeRequests = () => {
  router.push('/admin/merge-requests')
}

onMounted(() => {
  loadStats()
})

onUnmounted(() => {
  // 清理所有轮询任务
  taskPollingIntervals.forEach((intervalId) => {
    clearTimeout(intervalId)
  })
  taskPollingIntervals.clear()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 96vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  margin-bottom: 20px;
  flex-shrink: 0;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.title-icon {
  font-size: 28px;
  color: #409eff;
}

.stats-section {
  margin-bottom: 20px;
  flex-shrink: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 桌面端固定3列，形成3x3布局 */
  gap: 24px;
  margin-bottom: 24px;
}

.stats-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
  height: 100%;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stats-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 10px;
  font-size: 20px;
  color: white;
}

.projects-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.merge-requests-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.opened-icon {
  background: linear-gradient(135deg, #36d1dc, #5b86e5);
}

.reviewed-icon {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.pending-icon {
  background: linear-gradient(135deg, #ffd93d, #ff6b6b);
}

.tokens-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.today-reviews-icon {
  background: linear-gradient(135deg, #ff9a56, #ff6b6b);
}

.cache-tokens-icon {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.direct-tokens-icon {
  background: linear-gradient(135deg, #a8edea, #fed6e3);
}

.stats-content {
  flex: 1;
}

.stats-number {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.stats-subtitle {
  font-size: 12px;
  color: #c0c4cc;
  font-weight: 400;
  margin-top: 4px;
}

.actions-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}



.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.action-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.action-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 0;
}

.action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-size: 24px;
}

.sync-action-card .action-icon {
  background: linear-gradient(135deg, #ff9a56, #ff6b6b);
}

.sync-action-card.syncing .action-icon {
  background: linear-gradient(135deg, #409eff, #36a3f7);
  animation: pulse 1.5s ease-in-out infinite;
}

.sync-action-card.disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.sync-action-card.disabled:hover {
  transform: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #e4e7ed;
}

.sync-icon {
  transition: all 0.3s ease;
}

.sync-icon.syncing {
  animation: rotateArrow 1s linear infinite;
}

.action-card:nth-child(3) .action-icon {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.action-card:nth-child(4) .action-icon {
  background: linear-gradient(135deg, #a8edea, #fed6e3);
}

.action-text {
  flex: 1;
}

.action-text h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.action-text p {
  margin: 0;
  font-size: 14px;
  color: #909399;
  line-height: 1.5;
}

.action-status {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 32px;
}


.sync-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.progress-dots {
  display: flex;
  gap: 4px;
}

.progress-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #409eff;
  animation: dotPulse 1.4s ease-in-out infinite both;
}

.progress-dots .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.progress-dots .dot:nth-child(2) {
  animation-delay: -0.16s;
}

.progress-dots .dot:nth-child(3) {
  animation-delay: 0s;
}

.progress-text {
  font-size: 12px;
  color: #409eff;
  font-weight: 500;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes rotateArrow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes dotPulse {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr); /* 中屏退化为2列 */
    gap: 20px;
  }
  
  .actions-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stats-card {
    padding: 16px;
  }
  
  .stats-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }
  
  .stats-number {
    font-size: 24px;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .action-content {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .card-title {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .dashboard-container {
    padding: 12px;
  }
  
  .stats-grid {
    gap: 12px;
  }
  
  .stats-card {
    padding: 12px;
  }
  
  .stats-icon {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
  
  .stats-number {
    font-size: 20px;
  }
  
  .stats-label {
    font-size: 12px;
  }
  
  .actions-grid {
    gap: 12px;
  }
  
  .action-content {
    gap: 12px;
  }
  
  .action-text h3 {
    font-size: 16px;
  }
  
  .action-text p {
    font-size: 12px;
  }
}
</style>
