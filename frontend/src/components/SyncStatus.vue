<template>
  <div class="sync-status">
    <el-card class="sync-card">
      <template #header>
        <div class="card-header">
          <span>同步状态</span>
          <el-button 
            type="primary" 
            size="small" 
            @click="refreshStatus"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </template>
      
      <div class="status-content">
        <!-- 同步策略状态 -->
        <div class="status-section">
          <h4>同步策略</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="策略类型">
              <el-tag :type="syncStrategy.type === 'full' ? 'danger' : 'success'">
                {{ syncStrategy.type === 'full' ? '全量同步' : '增量同步' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="策略原因">
              {{ syncStrategy.reason }}
            </el-descriptions-item>
            <el-descriptions-item label="最后同步时间" v-if="syncStrategy.last_sync_time">
              {{ formatTime(syncStrategy.last_sync_time) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 调度器状态 -->
        <div class="status-section">
          <h4>调度器状态</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="运行状态">
              <el-tag :type="schedulerStatus.is_running ? 'success' : 'info'">
                {{ schedulerStatus.is_running ? '运行中' : '已停止' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="同步间隔">
              {{ formatInterval(schedulerStatus.sync_interval_seconds) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后同步时间" v-if="schedulerStatus.last_sync_time">
              {{ formatTime(schedulerStatus.last_sync_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="下次同步时间" v-if="schedulerStatus.next_sync_time">
              {{ formatTime(schedulerStatus.next_sync_time) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 操作按钮 -->
        <div class="action-section">
          <el-button 
            type="primary" 
            @click="runOptimizedSync"
            :loading="syncLoading"
          >
            执行优化同步
          </el-button>
          
          <el-button 
            type="success" 
            @click="startScheduler"
            :disabled="schedulerStatus.is_running"
            :loading="schedulerLoading"
          >
            启动调度器
          </el-button>
          
          <el-button 
            type="warning" 
            @click="stopScheduler"
            :disabled="!schedulerStatus.is_running"
            :loading="schedulerLoading"
          >
            停止调度器
          </el-button>
          
          <el-button 
            type="info" 
            @click="runSyncNow"
            :loading="syncLoading"
          >
            立即同步
          </el-button>
        </div>

        <!-- 需要审查的MR -->
        <div class="status-section" v-if="mrsNeedingReview.length > 0">
          <h4>需要审查的MR ({{ mrsNeedingReview.length }})</h4>
          <el-table :data="mrsNeedingReview" style="width: 100%">
            <el-table-column prop="title" label="标题" width="300" align="center" header-align="center" />
            <el-table-column prop="author" label="作者" width="120" align="center" header-align="center" />
            <el-table-column prop="project.name" label="项目" width="150" align="center" header-align="center" />
            <el-table-column prop="last_commit_sha" label="最新Commit" width="120" align="center" header-align="center">
              <template #default="scope">
                <el-tooltip :content="scope.row.last_commit_sha" placement="top">
                  <span>{{ scope.row.last_commit_sha?.substring(0, 8) || 'N/A' }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="180" align="center" header-align="center">
              <template #default="scope">
                {{ formatTime(scope.row.updated_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api/admin'

// 响应式数据
const loading = ref(false)
const syncLoading = ref(false)
const schedulerLoading = ref(false)

const syncStrategy = ref({
  type: '',
  reason: '',
  last_sync_time: null
})

const schedulerStatus = ref({
  is_running: false,
  sync_interval_seconds: 0,
  last_sync_time: null,
  next_sync_time: null
})

const mrsNeedingReview = ref<any[]>([])

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return 'N/A'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 格式化间隔时间
const formatInterval = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes} 分钟`
  }
  const hours = Math.floor(minutes / 60)
  return `${hours} 小时 ${minutes % 60} 分钟`
}

// 刷新状态
const refreshStatus = async () => {
  loading.value = true
  try {
    // 获取同步状态
    const syncResponse = await adminApi.getSyncStatus()
    syncStrategy.value = syncResponse.sync_strategy

    // 获取调度器状态
    const schedulerResponse = await adminApi.getSchedulerStatus()
    schedulerStatus.value = schedulerResponse.scheduler_status

    // 获取需要审查的MR
    const mrsResponse = await adminApi.getMrsNeedingReview()
    mrsNeedingReview.value = mrsResponse.mrs || []

    ElMessage.success('状态刷新成功')
  } catch (error) {
    console.error('刷新状态失败:', error)
    ElMessage.error('刷新状态失败')
  } finally {
    loading.value = false
  }
}

// 执行优化同步（异步任务模式）
const runOptimizedSync = async () => {
  syncLoading.value = true
  try {
    const response = await adminApi.syncGitLabData()
    if (response.success) {
      ElMessage.success(response.message || 'GitLab数据同步任务已提交，正在后台执行')
      // 开始轮询任务状态
      if (response.task_id) {
        pollTaskStatus(response.task_id)
      }
    } else {
      ElMessage.error(response.message || '提交同步任务失败')
    }
  } catch (error) {
    console.error('执行优化同步失败:', error)
    ElMessage.error('执行优化同步失败')
  } finally {
    syncLoading.value = false
  }
}

// 启动调度器
const startScheduler = async () => {
  schedulerLoading.value = true
  try {
    const response = await adminApi.startScheduler()
    ElMessage.success(response.message || '调度器启动成功')
    await refreshStatus()
  } catch (error) {
    console.error('启动调度器失败:', error)
    ElMessage.error('启动调度器失败')
  } finally {
    schedulerLoading.value = false
  }
}

// 停止调度器
const stopScheduler = async () => {
  schedulerLoading.value = true
  try {
    const response = await adminApi.stopScheduler()
    ElMessage.success(response.message || '调度器停止成功')
    await refreshStatus()
  } catch (error) {
    console.error('停止调度器失败:', error)
    ElMessage.error('停止调度器失败')
  } finally {
    schedulerLoading.value = false
  }
}

// 任务状态轮询
const taskPollingIntervals = new Map<string, number>()

const pollTaskStatus = async (taskId: string) => {
  try {
    const response = await adminApi.getTaskStatus(taskId)
    
    if (response.success) {
      const { status, progress, message, result, error } = response
      
      // 只在任务完成或失败时显示消息，避免频繁弹窗
      if (status === 'completed') {
        ElMessage.success('同步任务完成')
        // 清除轮询
        clearTaskPolling(taskId)
        // 刷新状态
        await refreshStatus()
      } else if (status === 'failed') {
        ElMessage.error(`同步任务失败: ${error || message}`)
        // 清除轮询
        clearTaskPolling(taskId)
      } else if (status === 'cancelled') {
        ElMessage.warning('同步任务已取消')
        // 清除轮询
        clearTaskPolling(taskId)
      }
      
      // 如果任务还在运行，继续轮询
      if (status === 'running' || status === 'pending') {
        const intervalId = setTimeout(() => {
          pollTaskStatus(taskId)
        }, 3000) // 每3秒轮询一次，减少频率
        taskPollingIntervals.set(taskId, intervalId)
      }
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
    ElMessage.error('获取任务状态失败')
    clearTaskPolling(taskId)
  }
}

const clearTaskPolling = (taskId: string) => {
  const intervalId = taskPollingIntervals.get(taskId)
  if (intervalId) {
    clearTimeout(intervalId)
    taskPollingIntervals.delete(taskId)
  }
}

// 取消任务
const cancelTask = async (taskId: string) => {
  try {
    const response = await adminApi.cancelTask(taskId)
    if (response.success) {
      ElMessage.success('任务已取消')
      clearTaskPolling(taskId)
    } else {
      ElMessage.error('取消任务失败')
    }
  } catch (error) {
    console.error('取消任务失败:', error)
    ElMessage.error('取消任务失败')
  }
}

// 立即同步
const runSyncNow = async () => {
  syncLoading.value = true
  try {
    const response = await adminApi.runSyncNow()
    ElMessage.success(response.message || '立即同步执行成功')
    await refreshStatus()
  } catch (error) {
    console.error('立即同步失败:', error)
    ElMessage.error('立即同步失败')
  } finally {
    syncLoading.value = false
  }
}

// 组件挂载时刷新状态
onMounted(() => {
  refreshStatus()
})
</script>

<style scoped>
.sync-status {
  padding: 20px;
}

.sync-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-section {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 16px;
}

.status-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.action-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-section .el-button {
  min-width: 120px;
}
</style>
