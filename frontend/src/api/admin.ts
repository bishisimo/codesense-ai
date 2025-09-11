import request from './index'

export interface Stats {
  total_projects: number
  total_merge_requests: number
  reviewed_merge_requests: number
  pending_merge_requests: number
  opened_merge_requests: number
  total_tokens: number
  monthly_tokens: number
  total_direct_tokens: number
  total_cache_tokens: number
  monthly_direct_tokens: number
  monthly_cache_tokens: number
  today_reviews: number
}

export interface MergeRequestListItem {
  id: number
  gitlab_id: number
  title: string
  author: string
  source_branch: string
  target_branch: string
  state: string
  mr_created_at: string
  mr_updated_at: string
  commits_count: number
  changes_count: number
  additions_count: number
  deletions_count: number
  project_name: string
  project_web_url: string
  review_status: string
  review_score?: number
  review_id?: number
  is_reviewed?: number  // 是否已审查：0=未审查，1=已审查
  is_latest_reviewed?: number  // 是否最新提交已审查：0=未审查，1=已审查
  is_reviewing?: number  // 是否正在审查中：0=非审查中，1=已审查
  is_failed?: number  // 是否审查失败：0=非失败，1=失败
  last_commit_sha?: string
  commit_id?: string  // 简短的commit ID（前8位）
}

export interface MergeRequestListResponse {
  items: MergeRequestListItem[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ReviewResult {
  success: boolean
  message: string
  review_id?: number
}

export interface ReviewTaskResponse {
  success: boolean
  task_id?: string
  message: string
  review_id?: number
  status?: string
}

export interface TaskStatus {
  task_id: string
  status: string
  result: any
  error: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  progress: number
  message: string
}

export interface ReviewHistoryItem {
  id: number
  commit_sha: string
  commit_sha_short: string
  score?: number
  status: string
  reviewer_type: string
  tokens_used?: number
  created_at: string
  updated_at: string
  is_latest: boolean
  comments_count: number
  is_reviewing: boolean
}

export interface ReviewHistoryResponse {
  merge_request_id: number
  merge_request_title: string
  latest_commit_sha?: string
  reviews: ReviewHistoryItem[]
  total: number
}

export interface Project {
  id: number
  name: string
  gitlab_id: number
  web_url: string
}

export interface ProjectListResponse {
  items: Project[]
}

export const adminApi = {
  // 获取项目列表
  getProjects: (): Promise<ProjectListResponse> => {
    return request({
      url: '/dashboard/projects',
      method: 'GET'
    })
  },

  // 获取统计信息
  getStats: (): Promise<Stats> => {
    return request({
      url: '/dashboard/stats',
      method: 'GET'
    })
  },

  // 获取合并请求列表
  getMergeRequests: (params: {
    page?: number
    size?: number
    project_id?: number
    author?: string
    source_branch?: string
    target_branch?: string
    state?: string
    sort_by?: string
    sort_order?: string
  }): Promise<MergeRequestListResponse> => {
    return request({
      url: '/merge-requests',
      method: 'GET',
      params
    })
  },

  // 获取单个合并请求状态
  getMergeRequestStatus: (mrId: number): Promise<{
    id: number
    gitlab_id: number
    title: string
    state: string
    review_status: string
    review_score?: number
    review_id?: number
    is_reviewed: number
    is_latest_reviewed: number
    is_reviewing: number
    is_failed: number
    last_commit_sha?: string
    updated_at?: string
    mr_updated_at?: string
  }> => {
    return request({
      url: `/merge-requests/${mrId}/status`,
      method: 'GET'
    })
  },

  // 手动触发代码审查（异步任务）
  triggerReview: (mrId: number, options: {
    force?: boolean
    template_id?: number
    custom_instructions?: string
  } = {}): Promise<ReviewTaskResponse> => {
    return request({
      url: `/reviews/merge-requests/${mrId}/trigger`,
      method: 'POST',
      params: {
        force: options.force || false,
        template_id: options.template_id,
        custom_instructions: options.custom_instructions || ''
      }
    })
  },

  // 查询审查任务状态
  getReviewTaskStatus: (taskId: string): Promise<TaskStatus> => {
    return request({
      url: `/reviews/tasks/${taskId}/status`,
      method: 'GET'
    })
  },

  // 获取审查任务结果
  getReviewTaskResult: (taskId: string): Promise<ReviewResult> => {
    return request({
      url: `/reviews/tasks/${taskId}/result`,
      method: 'GET'
    })
  },

  // 取消审查任务
  cancelReviewTask: (taskId: string): Promise<{ message: string }> => {
    return request({
      url: `/reviews/tasks/${taskId}/cancel`,
      method: 'POST'
    })
  },

  // 获取审查模板列表
  getReviewTemplates: (): Promise<{
    items: Array<{
      id: number
      name: string
      description: string
      is_active: boolean
    }>
  }> => {
    return request({
      url: '/prompt-templates',
      method: 'GET',
      params: { is_active: true, size: 100 }
    })
  },

  // 获取合并请求的审查历史
  getMergeRequestReviews: (mrId: number): Promise<ReviewHistoryResponse> => {
    return request({
      url: `/reviews/merge-requests/${mrId}/history`,
      method: 'GET'
    })
  },

  // 同步单个合并请求（同步执行）
  syncSingleMergeRequest: (mrId: number): Promise<{ success: boolean; message: string; mr_id: number; status: string; details?: any }> => {
    return request({
      url: `/sync/merge-requests/${mrId}`,
      method: 'POST'
    })
  },

  // 同步GitLab数据（异步任务）
  syncGitLabData: (): Promise<{ message: string; success: boolean; task_id: string; status: string }> => {
    return request({
      url: '/sync',
      method: 'POST'
    })
  },

  // 同步指定项目（异步任务）
  syncProject: (projectId: number): Promise<{ success: boolean; message: string; task_id: string; project_id: number; status: string }> => {
    return request({
      url: `/sync/projects/${projectId}`,
      method: 'POST'
    })
  },

  // 同步本地仓库（异步任务）
  syncRepositories: (): Promise<{ success: boolean; message: string; task_id: string; status: string }> => {
    return request({
      url: '/sync/repositories',
      method: 'POST'
    })
  },

  // 优化同步相关API
  syncOptimized: (): Promise<{ message: string; success: boolean; strategy?: string; details?: any }> => {
    return request({
      url: '/sync',
      method: 'POST'
    })
  },

  getSyncStatus: (): Promise<{ sync_strategy: any; message: string }> => {
    return request({
      url: '/sync/status',
      method: 'GET'
    })
  },

  getMrsNeedingReview: (): Promise<{ success: boolean; mrs: any[]; count: number }> => {
    return request({
      url: '/merge-requests/needing-review',
      method: 'GET'
    })
  },

  // 调度器相关API
  getSchedulerStatus: (): Promise<{ success: boolean; scheduler_status: any }> => {
    return request({
      url: '/scheduler/status',
      method: 'GET'
    })
  },

  startScheduler: (): Promise<{ success: boolean; message: string }> => {
    return request({
      url: '/scheduler/start',
      method: 'POST'
    })
  },

  stopScheduler: (): Promise<{ success: boolean; message: string }> => {
    return request({
      url: '/scheduler/stop',
      method: 'POST'
    })
  },

  runSyncNow: (): Promise<{ success: boolean; message: string; details?: any }> => {
    return request({
      url: '/scheduler/sync-now',
      method: 'POST'
    })
  },

  setSyncInterval: (intervalSeconds: number): Promise<{ success: boolean; message: string }> => {
    return request({
      url: '/scheduler/interval',
      method: 'PUT',
      params: { interval_minutes: Math.floor(intervalSeconds / 60) }
    })
  },

  // ==================== 异步任务状态查询API ====================
  
  // 获取任务状态
  getTaskStatus: (taskId: string): Promise<{
    success: boolean
    task_id: string
    status: string
    progress: number
    message: string
    started_at?: string
    completed_at?: string
    result?: any
    error?: string
  }> => {
    return request({
      url: `/sync/tasks/${taskId}`,
      method: 'GET'
    })
  },

  // 取消任务
  cancelTask: (taskId: string): Promise<{ success: boolean; message: string; task_id: string }> => {
    return request({
      url: `/sync/tasks/${taskId}`,
      method: 'DELETE'
    })
  }
}
