<template>
  <div class="merge-requests-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <!-- 预留空间，保持布局一致 -->
    </div>
    
    <!-- 项目选择器 -->
    <div class="project-selector-container">
      <div class="project-selector-content">
        <div class="selector-label">
          <el-icon class="label-icon"><Folder /></el-icon>
          <span>选择项目</span>
        </div>
        <el-select
          v-model="selectedProjectId"
          placeholder="请选择项目"
          clearable
          @change="handleProjectChange"
          class="modern-project-select"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
            class="project-option"
          >
            <div class="project-option-content">
              <div class="project-info">
                <div class="project-name">{{ project.name }}</div>
                <div class="project-meta">
                  <span class="project-id">#{{ project.gitlab_id }}</span>
                </div>
              </div>
              <div class="project-indicator">
                <div class="indicator-dot"></div>
              </div>
            </div>
          </el-option>
        </el-select>
        <!-- 同步项目按钮 -->
        <el-button 
          v-if="selectedProjectId"
          type="primary" 
          @click="syncProject" 
          :loading="syncLoading" 
          :disabled="currentProjectSyncStatus?.status === 'running'"
          size="small"
          class="sync-project-btn"
        >
          <el-icon v-if="!currentProjectSyncStatus || currentProjectSyncStatus.status !== 'running'"><Refresh /></el-icon>
          <span v-if="!currentProjectSyncStatus">同步项目</span>
          <span v-else-if="currentProjectSyncStatus.status === 'running'">
            同步中...
          </span>
          <span v-else>同步项目</span>
        </el-button>
      </div>
    </div>

    <!-- 筛选表单 -->
    <div class="filter-container">
      <div class="filter-grid">
        <div class="filter-item">
          <el-input
            v-model="filterForm.title"
            placeholder="搜索标题"
            clearable
            @input="debouncedLoadData"
            @keyup.enter="loadData"
            class="compact-input"
          >
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <el-input
            v-model="filterForm.author"
            placeholder="搜索作者"
            clearable
            @input="debouncedLoadData"
            @keyup.enter="loadData"
            class="compact-input"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <el-input
            v-model="filterForm.source_branch"
            placeholder="搜索源分支"
            clearable
            @input="debouncedLoadData"
            @keyup.enter="loadData"
            class="compact-input"
          >
            <template #prefix>
              <el-icon><Share /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <el-input
            v-model="filterForm.target_branch"
            placeholder="搜索目标分支"
            clearable
            @input="debouncedLoadData"
            @keyup.enter="loadData"
            class="compact-input"
          >
            <template #prefix>
              <el-icon><Share /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-item">
          <el-select
            v-model="filterForm.state"
            placeholder="选择MR状态"
            clearable
            @change="debouncedLoadData"
            class="compact-input"
          >
            <el-option label="全部" value="" />
            <el-option label="开发" value="opened" />
            <el-option label="合并" value="merged" />
            <el-option label="关闭" value="closed" />
          </el-select>
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="loadData" :loading="loading" size="small">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter" size="small">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table 
        v-loading="tableLoading"
        :data="tableData"
        style="width: 100%"
        @sort-change="handleSortChange"
        class="modern-table"
        :header-cell-style="{ background: '#f8f9fa', color: '#606266' }"
        :max-height="tableMaxHeight"
        stripe
      >
        <!-- 审查状态列 -->
        <el-table-column label="审查状态" width="180" fixed="left" align="center" header-align="center">
          <template #default="{ row }">
            <el-dropdown 
              trigger="click" 
              placement="bottom-start"
              :disabled="reviewingIds.has(row.id)"
              @command="(command: string) => handleReviewCommand(command, row)"
            >
              <div class="status-cell" :class="{ 
                'clickable': canReview(row) || row.is_reviewing === 1,
                'reviewing': row.is_reviewing === 1
              }">
                <div class="status-icon" :class="getReviewStatusClass(row)">
                  <el-icon v-if="getReviewStatusDesc(row) === '正在审查中'"><Loading /></el-icon>
                  <el-icon v-else-if="getReviewStatusDesc(row) === '审查最新'"><Check /></el-icon>
                  <el-icon v-else-if="getReviewStatusDesc(row) === '审查过时'"><RefreshLeft /></el-icon>
                  <el-icon v-else-if="getReviewStatusDesc(row) === '等待审查'"><Clock /></el-icon>
                  <el-icon v-else><InfoFilled /></el-icon>
                </div>
                <div class="status-text">
                  <div class="status-label">{{ getReviewStatusText(row) }}</div>
                  <div class="status-desc">{{ getReviewStatusDesc(row) }}</div>
                </div>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="direct">
                    <span style="font-size: 16px; margin-right: 8px;">🚀</span>
                    直接审查
                  </el-dropdown-item>
                  <el-dropdown-item command="custom">
                    <span style="font-size: 16px; margin-right: 8px;">⚙️</span>
                    自定义审查
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
        
        <!-- 评分列 -->
        <el-table-column label="评分" width="100" fixed="left" align="center" header-align="center">
          <template #default="{ row }">
            <div class="score-cell">
              <!-- 只有有review_id且有评分的才显示为可点击 -->
              <div v-if="row.review_score !== null && row.review_id && row.review_id > 0" 
                   class="score-badge clickable" 
                   :class="getScoreClass(row.review_score)"
                   @click="showReviewReport(row)"
                   title="点击查看审查报告">
                <span class="score-value">{{ row.review_score }}</span>
                <el-icon class="score-icon"><View /></el-icon>
              </div>
              <!-- 有评分但没有review_id的显示为不可点击 -->
              <div v-else-if="row.review_score !== null" 
                   class="score-badge" 
                   :class="getScoreClass(row.review_score)">
                <span class="score-value">{{ row.review_score }}</span>
              </div>
              <div v-else class="score-empty">
                <el-icon><Minus /></el-icon>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <!-- 其他列 -->
        <el-table-column prop="gitlab_id" label="MR ID" width="80" align="center" header-align="center">
          <template #default="{ row }">
            <div class="mr-id-cell">
              <span 
                class="mr-id-link" 
                @click="openGitLabInNewTab(row)"
                title="点击在新标签页中打开GitLab页面"
              >
                #{{ row.gitlab_id }}
                <el-icon class="link-icon"><Link /></el-icon>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" align="center" header-align="center" show-overflow-tooltip />
        <el-table-column prop="author" label="开发者" width="120" align="center" header-align="center" />
        <el-table-column prop="source_branch" label="源分支" width="150" align="center" header-align="center" show-overflow-tooltip />
        <el-table-column prop="target_branch" label="目标分支" width="150" align="center" header-align="center" show-overflow-tooltip />
        <el-table-column prop="state" label="状态" width="80" align="center" header-align="center">
          <template #default="{ row }">
            <el-tag :type="getStateType(row.state)" size="small" class="state-tag">
              {{ getStateText(row.state) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="commits_count" label="提交数" width="80" align="center" header-align="center" />
        <el-table-column label="改动行数" width="120" align="center" header-align="center">
          <template #default="{ row }">
            <span v-if="row.additions_count > 0 || row.deletions_count > 0">
              <span class="additions">+{{ row.additions_count }}</span>
              <span class="deletions">-{{ row.deletions_count }}</span>
            </span>
            <span v-else class="no-changes">0</span>
          </template>
        </el-table-column>
        <el-table-column label="Commit ID" width="100" align="center" header-align="center">
          <template #default="{ row }">
            <div v-if="row.commit_id" class="commit-id-cell">
              <span class="commit-id-text">{{ row.commit_id }}</span>
            </div>
            <span v-else class="no-commit">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="mr_created_at" label="MR创建时间" width="180" align="center" header-align="center" sortable="custom">
          <template #default="{ row }">
            {{ formatDate(row.mr_created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="mr_updated_at" label="MR更新时间" width="180" align="center" header-align="center" sortable="custom">
          <template #default="{ row }">
            {{ formatDate(row.mr_updated_at) }}
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="120" fixed="right" align="center" header-align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                type="warning" 
                size="small" 
                :loading="syncingIds.has(row.id)"
                @click="handleSync(row)"
                class="action-btn"
              >
                <el-icon v-if="!syncingIds.has(row.id)"><Refresh /></el-icon>
                {{ syncingIds.has(row.id) ? '同步中...' : '同步' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <div class="pagination-row">
          <div class="pagination-info">
            <span class="pagination-text">
              共 {{ pagination.total }} 条记录，每页显示 10 条
            </span>
          </div>
          <div class="pagination-controls">
            <el-pagination
              v-model:current-page="pagination.page"
              :total="pagination.total"
              :page-size="10"
              layout="prev, pager, next, jumper"
              @current-change="handleCurrentChange"
              class="modern-pagination"
            />
          </div>
        </div>
      </div>
    </el-card>




  </div>

  <!-- 自定义审查对话框 -->
  <CustomReviewDialog
    v-model="showCustomReviewDialog"
    :mr-id="currentReviewMR?.id || 0"
    :mr-title="currentReviewMR?.title || ''"
    :is-reviewing="currentReviewMR?.is_reviewing === 1"
    @confirm="handleCustomReviewConfirm"
  />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, 
  Refresh, 
  Search, 
  RefreshLeft, 
  Folder, 
  User, 
  Share,
  Clock,
  Check,
  InfoFilled,
  Minus,
  Edit,
  Loading,
  Close,
  View,
  ArrowRight,
  Link,
  ArrowDown,
  Setting
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { adminApi, type MergeRequestListItem, type Project } from '@/api/admin'

import { useAuthStore } from '@/stores/auth'
import CustomReviewDialog from '@/components/CustomReviewDialog.vue'

const router = useRouter()
const loading = ref(false)
const tableLoading = ref(false) // 专门用于表格的loading状态
const syncLoading = ref(false) // 同步项目的loading状态
const reviewingIds = ref(new Set<number>())
const syncingIds = ref(new Set<number>())

// 表格高度控制
const tableMaxHeight = ref(600)

// 防抖相关
let loadDataTimeout: number | null = null

// 定时刷新相关
const pollingIntervals = ref(new Map<number, number>())
const pollingCounts = ref(new Map<number, number>()) // 记录每个MR的轮询次数
const maxPollingCount = 60 // 最大轮询次数（3分钟）

// 任务状态轮询相关
const taskPollingIntervals = new Map<string, number>()
const taskStatuses = ref(new Map<string, { status: string; progress: number; message: string }>())

// 数据状态比较相关
const lastDataSnapshot = ref<Map<number, any>>(new Map())
const dataChangeCount = ref(0)

// 自定义审查对话框相关
const showCustomReviewDialog = ref(false)
const currentReviewMR = ref<MergeRequestListItem | null>(null)

// 获取当前项目的同步状态
const currentProjectSyncStatus = computed(() => {
  for (const [taskId, status] of taskStatuses.value) {
    if (status.status === 'running' || status.status === 'pending') {
      return status
    }
  }
  return null
})

// 获取当前选中项目的名称
const currentProjectName = computed(() => {
  if (!selectedProjectId.value) return null
  const project = projects.value.find(p => p.id === selectedProjectId.value)
  return project?.name || null
})



// GitLab链接相关
const openGitLabInNewTab = (row: MergeRequestListItem) => {
  const gitlabUrl = `${row.project_web_url}/-/merge_requests/${row.gitlab_id}`
  window.open(gitlabUrl, '_blank')
}

const filterForm = reactive({
  title: '',
  author: '',
  source_branch: '',
  target_branch: '',
  state: ''
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const sortInfo = reactive({
  sort_by: 'mr_created_at',
  sort_order: 'desc'
})

const tableData = ref<MergeRequestListItem[]>([])

// 项目相关
const projects = ref<Project[]>([])
const selectedProjectId = ref<number | null>(null)

// 从localStorage加载选中的项目
const loadSelectedProject = () => {
  const savedProjectId = localStorage.getItem('selectedProjectId')
  if (savedProjectId) {
    selectedProjectId.value = parseInt(savedProjectId)
  }
}

// 保存选中的项目到localStorage
const saveSelectedProject = (projectId: number | null) => {
  if (projectId) {
    localStorage.setItem('selectedProjectId', projectId.toString())
  } else {
    localStorage.removeItem('selectedProjectId')
  }
}

// 保存分页状态到localStorage
const savePaginationState = () => {
  const paginationState = {
    page: pagination.page,
    size: pagination.size,
    total: pagination.total,
    filterForm: { ...filterForm },
    sortInfo: { ...sortInfo },
    selectedProjectId: selectedProjectId.value
  }
  localStorage.setItem('mergeRequestsPaginationState', JSON.stringify(paginationState))
}

// 从localStorage恢复分页状态
const restorePaginationState = () => {
  try {
    const savedState = localStorage.getItem('mergeRequestsPaginationState')
    if (savedState) {
      const state = JSON.parse(savedState)
      pagination.page = state.page || 1
      pagination.size = state.size || 10
      pagination.total = state.total || 0
      
      // 恢复筛选条件
      if (state.filterForm) {
        Object.assign(filterForm, state.filterForm)
      }
      
      // 恢复排序信息
      if (state.sortInfo) {
        Object.assign(sortInfo, state.sortInfo)
      }
      
      // 恢复选中的项目
      if (state.selectedProjectId) {
        selectedProjectId.value = state.selectedProjectId
      }
      
      // 清除保存的状态，避免影响其他操作
      localStorage.removeItem('mergeRequestsPaginationState')
      return true
    }
  } catch (error) {
    console.error('恢复分页状态失败:', error)
    localStorage.removeItem('mergeRequestsPaginationState')
  }
  return false
}

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await adminApi.getProjects()
    projects.value = response.items
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  }
}

// 处理项目选择变化
const handleProjectChange = (projectId: number | null) => {
  saveSelectedProject(projectId)
  pagination.page = 1 // 重置到第一页
  // 项目变化时立即加载，不使用防抖
  loadData(true)
}

// 同步指定项目（异步任务模式）
const syncProject = async () => {
  if (!selectedProjectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }

  try {
    syncLoading.value = true
    const result = await adminApi.syncProject(selectedProjectId.value)
    
    if (result.success) {
      const projectName = currentProjectName.value || `项目 ${selectedProjectId.value}`
      ElMessage.success(`${projectName} 同步任务已提交，正在后台执行`)
      // 开始轮询任务状态
      if (result.task_id) {
        // 初始化任务状态
        taskStatuses.value.set(result.task_id, { 
          status: 'pending', 
          progress: 0, 
          message: '任务已提交，等待执行...' 
        })
        pollTaskStatus(result.task_id)
      }
    } else {
      ElMessage.error(result.message || '提交同步任务失败')
    }
  } catch (error) {
    console.error('同步项目失败:', error)
    ElMessage.error('同步项目失败')
  } finally {
    syncLoading.value = false
  }
}

// 防抖的loadData函数
const debouncedLoadData = () => {
  if (loadDataTimeout) {
    clearTimeout(loadDataTimeout)
  }
  loadDataTimeout = setTimeout(() => {
    loadData(true)
  }, 300) // 300ms防抖延迟
}

// 比较数据是否发生变化
const hasDataChanged = (newData: MergeRequestListItem[], oldData: Map<number, any>): boolean => {
  if (newData.length !== oldData.size) {
    return true
  }
  
  for (const item of newData) {
    const oldItem = oldData.get(item.id)
    if (!oldItem) {
      return true
    }
    
    // 比较关键字段，重点关注审查相关状态
    const keyFields = [
      'is_reviewing', 
      'is_reviewed', 
      'is_latest_reviewed', 
      'is_failed',
      'review_status', 
      'review_score',
      'review_id',
      'last_commit_sha', 
      'state',
      'updated_at',
      'mr_updated_at'
    ]
    for (const field of keyFields) {
      if ((item as any)[field] !== (oldItem as any)[field]) {
        return true
      }
    }
  }
  
  return false
}

// 更新数据快照
const updateDataSnapshot = (data: MergeRequestListItem[]) => {
  const snapshot = new Map<number, any>()
  data.forEach(item => {
    snapshot.set(item.id, {
      is_reviewing: item.is_reviewing,
      is_reviewed: item.is_reviewed,
      is_latest_reviewed: item.is_latest_reviewed,
      is_failed: item.is_failed,
      review_status: item.review_status,
      review_score: item.review_score,
      review_id: item.review_id,
      mr_updated_at: item.mr_updated_at,
      last_commit_sha: item.last_commit_sha,
      state: item.state
    })
  })
  lastDataSnapshot.value = snapshot
}

const loadData = async (forceRefresh: boolean = false) => {
  try {
    tableLoading.value = true
    const params: Record<string, any> = {
      page: pagination.page,
      size: pagination.size,
      ...filterForm,
      ...sortInfo
    }
    
    // 添加项目ID筛选
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await adminApi.getMergeRequests(params)
    
    // 检查数据是否发生变化
    if (!forceRefresh && hasDataChanged(response.items, lastDataSnapshot.value)) {
      dataChangeCount.value++
      console.log(`数据发生变化，第${dataChangeCount.value}次更新`)
    } else if (!forceRefresh) {
      console.log('数据未发生变化，跳过前端更新')
      return
    }
    
    tableData.value = response.items
    pagination.total = response.total
    
    // 更新数据快照
    updateDataSnapshot(response.items)
    
    // 调试信息
    console.log('API请求参数:', params)
    console.log('API响应:', {
      total: response.total,
      page: response.page,
      size: response.size,
      pages: response.pages,
      itemsCount: response.items.length
    })
    
    // 确保页码不超出范围
    const totalPages = Math.ceil(response.total / pagination.size)
    if (pagination.page > totalPages && totalPages > 0) {
      pagination.page = totalPages
      // 重新加载数据
      await loadData(true)
      return
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    tableLoading.value = false
  }
}



const resetFilter = () => {
  Object.keys(filterForm).forEach(key => {
    (filterForm as Record<string, string>)[key] = ''
  })
  pagination.page = 1
  loadData(true)
}

const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  if (order) {
    sortInfo.sort_by = prop
    sortInfo.sort_order = order === 'ascending' ? 'asc' : 'desc'
  } else {
    sortInfo.sort_by = 'mr_created_at'
    sortInfo.sort_order = 'desc'
  }
  loadData(true)
}



const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadData(true)
}

const viewReport = (row: MergeRequestListItem) => {
  // 跳转到审查详情页面
  if (row.review_id) {
    // 保存当前分页状态
    savePaginationState()
    router.push(`/admin/review/${row.review_id}`)
  } else {
    ElMessage.warning('该合并请求暂无审查报告')
  }
}

const showReviewReport = (row: MergeRequestListItem) => {
  // 直接跳转到完整报告界面
  if (row.review_id && row.review_id > 0) {
    // 保存当前分页状态
    savePaginationState()
    router.push(`/admin/review/${row.review_id}`)
  } else {
    if (row.review_status === '未审查') {
      ElMessage.warning('该合并请求尚未进行代码审查，请先点击"代码审查"按钮')
    } else if (row.review_status === '审查进行中') {
      ElMessage.info('审查正在进行中，请稍后再试')
    } else if (row.review_status === '审查失败') {
      ElMessage.error('审查失败，请重新触发审查')
    } else {
      ElMessage.warning('该合并请求暂无审查报告')
    }
  }
}



// 检查是否可以审查
const canReview = (row: MergeRequestListItem) => {
  // 如果正在审查中，则不可点击
  if (reviewingIds.value.has(row.id)) {
    return false
  }
  
  // 如果后端显示正在审查中，也不可点击（避免显示下拉箭头）
  if (row.is_reviewing === 1) {
    return false
  }
  
  return true
}


// 处理审查下拉菜单命令
const handleReviewCommand = async (command: string, row: MergeRequestListItem) => {
  // 如果正在审查中，不执行任何操作
  if (reviewingIds.value.has(row.id)) {
    return
  }
  
  // 如果后端显示正在审查中，显示强制审查警告
  if (row.is_reviewing === 1) {
    try {
      await ElMessageBox.confirm(
        `合并请求 ${row.gitlab_id} 正在审查中，强制重新审查将中断当前审查。是否继续？`,
        '强制审查警告',
        {
          confirmButtonText: '强制审查',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
    } catch (error) {
      // 用户取消
      return
    }
  }
  
  if (command === 'direct') {
    // 直接审查
    await executeReview(row, { force: row.is_reviewing === 1 })
  } else if (command === 'custom') {
    // 自定义审查，直接显示自定义审查对话框
    currentReviewMR.value = row
    showCustomReviewDialog.value = true
  }
}

// 执行审查
const executeReview = async (row: MergeRequestListItem, options: {
  force: boolean
  template_id?: number
  custom_instructions?: string
}) => {
  try {
    reviewingIds.value.add(row.id)
    const result = await adminApi.triggerReview(row.id, options)
    
    // 检查是否成功启动审查
    if (result.success) {
      ElMessage.success(result.message || '代码审查已启动，正在处理中...')
      
      // 立即刷新数据，显示审查中状态
      await loadData(true)
      
      // 启动状态轮询
      startPollingForReviewStatus(row.id)
    } else {
      ElMessage.error(result.message || '启动代码审查失败')
    }
  } catch (error: any) {
    if (error.response?.status === 409) {
      ElMessage.warning('该合并请求正在审查中，请稍后再试')
    } else {
      ElMessage.error('操作失败')
    }
  } finally {
    reviewingIds.value.delete(row.id)
  }
}

// 处理自定义审查确认
const handleCustomReviewConfirm = async (options: {
  force: boolean
  template_id?: number
  custom_instructions?: string
}) => {
  if (!currentReviewMR.value) return
  
  const row = currentReviewMR.value
  await executeReview(row, options)
}

const handleSync = async (row: MergeRequestListItem) => {
  try {
    syncingIds.value.add(row.id)
    const result = await adminApi.syncSingleMergeRequest(row.id)
    
    if (result.success) {
      // 同步执行完成，直接重新加载数据，不显示弹窗
      await loadData(true)
    } else {
      ElMessage.error(result.message || '同步失败')
    }
  } catch (error) {
    console.error('同步失败:', error)
    ElMessage.error('同步失败')
  } finally {
    syncingIds.value.delete(row.id)
  }
}

// 任务状态轮询
const pollTaskStatus = async (taskId: string) => {
  try {
    const response = await adminApi.getTaskStatus(taskId)
    
    if (response.success) {
      const { status, progress, message, result, error } = response
      
      // 更新任务状态
      taskStatuses.value.set(taskId, { status, progress, message })
      
      // 只在任务完成或失败时显示消息，避免频繁弹窗
      if (status === 'completed') {
        ElMessage.success('同步任务完成')
        // 清除轮询和状态
        clearTaskPolling(taskId)
        taskStatuses.value.delete(taskId)
        // 重新加载数据
        await loadData(true)
      } else if (status === 'failed') {
        ElMessage.error(`同步任务失败: ${error || message}`)
        // 清除轮询和状态
        clearTaskPolling(taskId)
        taskStatuses.value.delete(taskId)
      } else if (status === 'cancelled') {
        ElMessage.warning('同步任务已取消')
        // 清除轮询和状态
        clearTaskPolling(taskId)
        taskStatuses.value.delete(taskId)
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
    taskStatuses.value.delete(taskId)
  }
}

const clearTaskPolling = (taskId: string) => {
  const intervalId = taskPollingIntervals.get(taskId)
  if (intervalId) {
    clearTimeout(intervalId)
    taskPollingIntervals.delete(taskId)
  }
}

const getReviewStatusClass = (row: any) => {
  if (row.is_reviewing === 1) return 'status-reviewing'
  if (row.is_failed === 1) return 'status-error'  // 添加失败状态样式
  if (row.is_reviewed === 0) return 'status-pending'
  if (row.is_reviewed === 1 && row.is_latest_reviewed === 1) return 'status-success'
  if (row.is_reviewed === 1 && row.is_latest_reviewed === 0) return 'status-warning'
  return 'status-info'
}

const getReviewStatusText = (row: any) => {
  if (row.is_reviewing === 1) return '审查中'
  if (row.is_failed === 1) return '审查失败'  // 添加失败状态文本
  if (row.is_reviewed === 0) return '未审查'
  if (row.is_reviewed === 1) return '已审查'
  return '未审查'
}

const getReviewStatusDesc = (row: any) => {
  if (row.is_reviewing === 1) return '正在审查中'
  if (row.is_failed === 1) return '审查失败'  // 添加失败状态描述
  if (row.is_reviewed === 0) return '等待审查'
  if (row.is_reviewed === 1 && row.is_latest_reviewed === 1) return '审查最新'
  if (row.is_reviewed === 1 && row.is_latest_reviewed === 0) return '审查过时'
  return '等待审查'
}

// 检查是否有审查中的记录
const hasReviewingRecord = (row: any) => {
  // 这里需要根据实际数据结构来判断
  // 暂时返回false，后续可以通过API获取
  return false
}

// 更新单个MR的状态
const updateSingleMRStatus = async (mrId: number) => {
  try {
    const statusData = await adminApi.getMergeRequestStatus(mrId)
    
    // 找到对应的行并更新状态
    const mrIndex = tableData.value.findIndex(item => item.id === mrId)
    if (mrIndex !== -1) {
      const currentMR = tableData.value[mrIndex]
      
      // 检查状态是否真的发生了变化
      const hasChanged = (
        currentMR.is_reviewing !== statusData.is_reviewing ||
        currentMR.is_reviewed !== statusData.is_reviewed ||
        currentMR.is_latest_reviewed !== statusData.is_latest_reviewed ||
        currentMR.is_failed !== statusData.is_failed ||
        currentMR.review_status !== statusData.review_status ||
        currentMR.review_score !== statusData.review_score ||
        currentMR.last_commit_sha !== statusData.last_commit_sha ||
        currentMR.state !== statusData.state
      )
      
      if (hasChanged) {
        // 只更新变化的字段，避免不必要的重新渲染
        tableData.value[mrIndex] = {
          ...currentMR,
          is_reviewing: statusData.is_reviewing,
          is_reviewed: statusData.is_reviewed,
          is_latest_reviewed: statusData.is_latest_reviewed,
          is_failed: statusData.is_failed,
          review_status: statusData.review_status,
          review_score: statusData.review_score,
          last_commit_sha: statusData.last_commit_sha,
          state: statusData.state,
          review_id: statusData.review_id,
          mr_updated_at: statusData.mr_updated_at || currentMR.mr_updated_at
        }
        
        console.log(`MR ${mrId} 状态已更新:`, {
          is_reviewing: statusData.is_reviewing,
          review_status: statusData.review_status,
          review_score: statusData.review_score
        })
      }
    }
  } catch (error) {
    console.error(`更新MR ${mrId} 状态失败:`, error)
  }
}

// 启动定时刷新审查状态
const startPollingForReviewStatus = (mrId: number) => {
  // 清除之前的定时器
  stopPollingForReviewStatus(mrId)
  
  // 重置轮询计数
  pollingCounts.value.set(mrId, 0)
  
  // 启动新的定时器，每3秒检查一次
  const interval = setInterval(async () => {
    try {
      // 增加轮询计数
      const currentCount = pollingCounts.value.get(mrId) || 0
      pollingCounts.value.set(mrId, currentCount + 1)
      
      // 检查是否超过最大轮询次数
      if (currentCount >= maxPollingCount) {
        console.warn(`MR ${mrId} 轮询超时，停止轮询`)
        stopPollingForReviewStatus(mrId)
        return
      }
      
      // 只查询单个MR的状态，避免全表刷新
      await updateSingleMRStatus(mrId)
      
      // 检查该MR是否还在审查中
      const mr = tableData.value.find(item => item.id === mrId)
      if (mr && mr.is_reviewing !== 1) {
        // 如果不再审查中，停止定时刷新
        console.log(`MR ${mrId} 审查完成，停止轮询`)
        stopPollingForReviewStatus(mrId)
      }
    } catch (error) {
      console.error('定时刷新失败:', error)
      stopPollingForReviewStatus(mrId)
    }
  }, 3000)
  
  pollingIntervals.value.set(mrId, interval)
  console.log(`开始轮询MR ${mrId} 的审查状态`)
}

// 停止定时刷新
const stopPollingForReviewStatus = (mrId: number) => {
  const interval = pollingIntervals.value.get(mrId)
  if (interval) {
    clearInterval(interval)
    pollingIntervals.value.delete(mrId)
    pollingCounts.value.delete(mrId)
    console.log(`停止轮询MR ${mrId} 的审查状态`)
  }
}

// 清理所有定时器
const clearAllPolling = () => {
  pollingIntervals.value.forEach((interval) => {
    clearInterval(interval)
  })
  pollingIntervals.value.clear()
  pollingCounts.value.clear()
}



const getScoreClass = (score: number) => {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  return 'score-poor'
}

const getStateType = (state: string) => {
  const types: Record<string, string> = {
    opened: 'success',  // 开发状态改为绿色
    closed: 'info',     // 关闭状态保持灰色
    merged: 'primary'   // 合并状态改为蓝色
  }
  return types[state] || 'info'
}

const getStateText = (state: string) => {
  const texts: Record<string, string> = {
    opened: '开发',
    closed: '关闭',
    merged: '合并'
  }
  return texts[state] || state
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 计算表格最大高度
const calculateTableHeight = () => {
  // 计算10条数据的高度：表头(40px) + 10行数据(每行50px)
  const tableContentHeight = 60 + (11 * 60)
  // 设置表格最大高度为10条数据的高度
  tableMaxHeight.value = tableContentHeight
}

onMounted(async () => {
  await loadProjects()
  
  // 尝试恢复分页状态，如果没有保存的状态则使用默认的项目选择
  const hasRestoredState = restorePaginationState()
  if (!hasRestoredState) {
    loadSelectedProject()
  }
  
  loadData(true)
  
  // 计算表格高度
  calculateTableHeight()
  
  // 监听窗口大小变化
  window.addEventListener('resize', calculateTableHeight)
})

onUnmounted(() => {
  // 清理所有定时器
  clearAllPolling()
  
  // 移除窗口大小变化监听
  window.removeEventListener('resize', calculateTableHeight)
})
</script>

<style scoped>
.merge-requests-container {
  padding: 16px 24px 24px 24px;
  background: #f5f7fa;
  min-height: 96vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.project-selector-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e9ecef;
  position: relative;
  flex-shrink: 0;
}

.project-selector-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 20px;
}

.selector-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #606266;
  min-width: 90px;
  font-size: 14px;
  white-space: nowrap;
}

.label-icon {
  font-size: 16px;
  color: #909399;
}

.modern-project-select {
  min-width: 320px;
  flex: 1;
}

.modern-project-select :deep(.el-input__wrapper) {
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  transition: all 0.3s ease;
  height: 40px;
}

.modern-project-select :deep(.el-input__wrapper:hover) {
  border-color: #409eff;
}

.modern-project-select :deep(.el-input__inner) {
  color: #303133;
  font-weight: 500;
  font-size: 14px;
  line-height: 44px;
}

.modern-project-select :deep(.el-input__inner::placeholder) {
  color: #909399;
  font-weight: 400;
}

.project-option {
  padding: 12px 16px;
  transition: all 0.2s ease;
  line-height: 1.4;
  min-height: 48px;
}

.project-option:hover {
  background: linear-gradient(135deg, #f5f7fa 0%, #e3f2fd 100%);
}

.project-option-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 24px;
}

.project-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.project-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-meta {
  display: flex;
  align-items: center;
}

.project-id {
  color: #909399;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
}

.project-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-left: 8px;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  opacity: 0;
  transition: all 0.3s ease;
}

.project-option:hover .indicator-dot {
  opacity: 1;
  transform: scale(1.3);
}

.filter-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e9ecef;
  /* 防止筛选栏闪烁 */
  min-height: 80px;
  position: relative;
  z-index: 1;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  align-items: center;
  min-height: 48px;
}

.filter-item {
  min-width: 180px;
  /* 防止筛选项闪烁 */
  position: relative;
  z-index: 2;
}

.filter-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  grid-column: span 2;
  justify-content: flex-end;
}

.compact-input :deep(.el-input__wrapper) {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.compact-input :deep(.el-input__wrapper:hover) {
  border-color: #409eff;
}

.compact-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.compact-input :deep(.el-select .el-input__wrapper) {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.compact-input :deep(.el-select .el-input__wrapper:hover) {
  border-color: #409eff;
}

.compact-input :deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.filter-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.table-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

/* 表格滚动优化 */
:deep(.el-table__body-wrapper) {
  overflow-y: auto;
  overflow-x: auto;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: #c1c1c1;
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: #a8a8a8;
}

/* 固定列样式优化 */
:deep(.el-table__fixed) {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-table__fixed-right) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

/* 表格行悬停效果 */
:deep(.el-table__body tr:hover > td) {
  background-color: #f8f9fa !important;
}

/* 斑马纹样式优化 */
:deep(.el-table__body tr:nth-child(even)) {
  background-color: #fafbfc;
}

/* 表格行高度优化 */
:deep(.el-table__body tr) {
  height: 50px;
}

:deep(.el-table__header tr) {
  height: 40px;
}

/* 确保表格内容垂直居中 */
:deep(.el-table__body td) {
  padding: 8px 0;
  vertical-align: middle;
}

:deep(.el-table__header th) {
  padding: 8px 0;
  vertical-align: middle;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  transition: all 0.2s ease;
  min-width: 0; /* 防止内容溢出 */
  width: 100%;
  justify-content: center; /* 改为居中对齐，保持整体布局稳定 */
  position: relative; /* 为绝对定位的子元素提供参考 */
}

.status-cell.clickable {
  cursor: pointer;
  border-radius: 6px;
  padding: 4px 8px;
  transition: all 0.2s ease;
}

.status-cell.clickable:hover {
  background: rgba(64, 158, 255, 0.1);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 14px;
  color: white;
  flex-shrink: 0; /* 防止图标被压缩 */
  flex-grow: 0; /* 防止图标被拉伸 */
  position: absolute; /* 使用绝对定位确保位置固定 */
  left: 10px; /* 距离左侧10px，保持适当间距 */
  top: 50%; /* 垂直居中 */
  transform: translateY(-50%); /* 精确垂直居中 */
}

.status-reviewing {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  animation: pulse 2s infinite;
}

.status-pending {
  background: linear-gradient(135deg, #ff9a56, #ff6b6b);
}

.status-success {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.status-warning {
  background: linear-gradient(135deg, #ffd93d, #ff6b6b);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.status-error {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
}

.status-info {
  background: linear-gradient(135deg, #a8edea, #fed6e3);
}

.status-text {
  flex: 1;
  min-width: 0; /* 防止flex子元素溢出 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center; /* 改为居中对齐，保持文字位置稳定 */
  margin-left: 44px; /* 为绝对定位的图标留出空间 (10px + 28px + 6px) */
  width: calc(100% - 44px); /* 固定宽度，减去图标占用的空间 */
  position: relative; /* 为内部元素提供定位参考 */
}

.status-label {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%; /* 固定宽度 */
  text-align: center; /* 居中对齐 */
}

.status-desc {
  font-size: 11px;
  color: #909399;
  line-height: 1.2;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%; /* 固定宽度 */
  text-align: center; /* 居中对齐 */
}



.score-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-badge {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 16px;
  font-weight: 600;
  font-size: 14px;
  color: white;
  min-width: 50px;
  justify-content: center;
  position: relative;
  transition: all 0.2s ease;
}

.score-badge.clickable {
  cursor: pointer;
  padding-right: 28px;
  transition: all 0.2s ease;
}

.score-badge.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.score-icon {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.score-badge.clickable:hover .score-icon {
  opacity: 1;
}

.score-excellent {
  background: #10b981;
}

.score-good {
  background: #f59e0b;
}

.score-poor {
  background: #ef4444;
}

.score-value {
  font-size: 14px;
  font-weight: 600;
}

.score-empty {
  color: #c0c4cc;
  font-size: 16px;
}

.state-tag {
  border-radius: 12px;
  font-weight: 500;
  font-size: 12px;
  padding: 4px 8px;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 自定义状态颜色 */
.state-tag.el-tag--success {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.state-tag.el-tag--primary {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
}

.state-tag.el-tag--info {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
  color: white;
}

.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.action-btn {
  border-radius: 6px;
  font-weight: 500;
}

.additions {
  color: #67c23a;
  font-weight: 500;
  margin-right: 4px;
}

.deletions {
  color: #f56c6c;
  font-weight: 500;
}

.no-changes {
  color: #909399;
  font-style: italic;
}

.pagination-container {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.pagination-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
}

.pagination-info {
  display: flex;
  align-items: center;
}

.pagination-text {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pagination-sizes-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-size-select {
  width: 80px;
}

.page-size-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  border: 1px solid #dcdfe6;
}

.page-size-select :deep(.el-input__wrapper:hover) {
  border-color: #409eff;
}

.page-size-select :deep(.el-input__inner) {
  text-align: center;
  padding-right: 8px;
}

.page-size-select :deep(.el-input__suffix) {
  display: none;
}

.page-size-unit {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.modern-pagination {
  --el-pagination-bg-color: transparent;
  --el-pagination-border-radius: 8px;
}

.modern-pagination :deep(.el-pagination__sizes) {
  margin-right: 16px;
}

.modern-pagination :deep(.el-pagination__total) {
  margin-right: 16px;
}

.modern-pagination :deep(.el-pagination__jump) {
  margin-left: 16px;
}

.modern-pagination :deep(.el-select .el-input) {
  width: 100px;
}

.modern-pagination :deep(.el-pagination__jump .el-input) {
  width: 50px;
}

.modern-pagination :deep(.el-pagination__sizes .el-select .el-input__inner) {
  text-align: center;
  padding-right: 8px;
}

.modern-pagination :deep(.el-pagination__sizes .el-select .el-input__suffix) {
  display: none;
}

.modern-pagination :deep(.el-pagination__sizes .el-select .el-input__wrapper) {
  border-radius: 6px;
}

.modern-pagination :deep(.el-pagination__sizes .el-select .el-input__wrapper:hover) {
  border-color: #409eff;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  flex: 1;
}

:deep(.el-table th) {
  background: #f8f9fa !important;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-table td) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: #f5f7fa;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}

:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-pagination .el-pager li) {
  border-radius: 6px;
}

.mr-id-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.mr-id-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
  cursor: pointer;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  position: relative;
}

.mr-id-link:hover {
  background: rgba(64, 158, 255, 0.1);
  color: #66b1ff;
  transform: translateY(-1px);
}

.link-icon {
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.mr-id-link:hover .link-icon {
  opacity: 1;
}

.sync-project-btn {
  margin-left: 12px;
  transition: all 0.3s ease;
  background: #409eff;
  border: 1px solid #409eff;
  color: white;
  font-weight: 500;
  border-radius: 6px;
  height: 40px;
  padding: 0 16px;
}

.sync-project-btn:hover {
  background: #66b1ff;
  border-color: #66b1ff;
}

.sync-project-btn:active {
  background: #3a8ee6;
  border-color: #3a8ee6;
}

.commit-id-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #303133;
  font-weight: 500;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.commit-id-cell:hover {
  background: rgba(64, 158, 255, 0.1);
  color: #66b1ff;
  transform: translateY(-1px);
}

.commit-id-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-commit {
  color: #909399;
  font-style: italic;
}


/* 响应式设计 */
@media (max-width: 1200px) {
  .filter-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
  }
  
  .filter-actions {
    grid-column: span 1;
  }
  
  .project-selector-content {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .modern-project-select {
    width: 100%;
  }
  
  .sync-project-btn {
    margin-left: 0;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .merge-requests-container {
    padding: 16px;
  }
  
  .filter-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .filter-actions {
    grid-column: span 1;
    justify-content: stretch;
  }
  
  .filter-actions .el-button {
    flex: 1;
  }
  
  .project-selector-container {
    padding: 12px;
  }
  
  .project-selector-content {
    gap: 8px;
  }
  
  .selector-label {
    font-size: 14px;
  }
  
  .table-card {
    margin-top: 16px;
  }
  
  :deep(.el-table) {
    font-size: 12px;
  }
  
  :deep(.el-table th) {
    padding: 8px 4px;
  }
  
  :deep(.el-table td) {
    padding: 8px 4px;
  }
  
  .mr-id-link {
    padding: 2px 4px;
    font-size: 12px;
  }
  
  .score-badge {
    padding: 4px 8px;
    font-size: 12px;
    min-width: 40px;
  }
  
  .state-tag {
    font-size: 10px;
    padding: 2px 6px;
  }
}

@media (max-width: 480px) {
  .merge-requests-container {
    padding: 12px;
  }
  
  .filter-container {
    padding: 12px;
  }
  
  .filter-grid {
    gap: 8px;
  }
  
  .project-selector-container {
    padding: 8px;
  }
  
  .project-selector-content {
    gap: 6px;
  }
  
  .selector-label {
    font-size: 13px;
  }
  
  .table-card {
    margin-top: 12px;
  }
  
  :deep(.el-table) {
    font-size: 11px;
  }
  
  :deep(.el-table th) {
    padding: 6px 2px;
  }
  
  :deep(.el-table td) {
    padding: 6px 2px;
  }
  
  .mr-id-link {
    padding: 1px 3px;
    font-size: 11px;
  }
  
  .score-badge {
    padding: 3px 6px;
    font-size: 11px;
    min-width: 35px;
  }
  
  .state-tag {
    font-size: 9px;
    padding: 1px 4px;
  }
  
  /* 审查状态下拉菜单样式 */
  .status-cell {
    position: relative;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    border-radius: 6px;
    transition: all 0.3s ease;
  }
  
  .status-cell.clickable {
    cursor: pointer;
  }
  
  .status-cell.clickable:hover {
    background-color: #f0f9ff;
    border-color: #409eff;
  }
  
  .status-cell.reviewing {
    background-color: #fff7e6;
    border: 1px solid #ffd591;
  }
  
  .status-cell.reviewing:hover {
    background-color: #fff2e8;
    border-color: #ffa940;
  }
  
  
  :deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  :deep(.el-dropdown-menu__item .el-icon) {
    font-size: 14px;
  }
}
</style>
