import api from './index'

// 类型定义
export interface TimeRangeFilter {
  start_date?: string
  end_date?: string
  period?: 'today' | 'this_week' | 'this_month' | 'week' | 'month' | 'quarter' | 'year' | 'custom'
}

export interface ProjectStats {
  project_id: number
  project_name: string
  total_mrs: number
  merged_mrs: number
  open_mrs: number
  total_additions: number
  total_deletions: number
  net_changes: number
  avg_mr_size: number
  review_coverage: number
  code_growth_rate: number
  code_reduction_rate: number
  avg_additions_per_mr: number
  avg_deletions_per_mr: number
}

export interface UserStats {
  author: string
  total_mrs: number
  merged_mrs: number
  total_additions: number
  total_deletions: number
  net_changes: number
  avg_mr_size: number
  avg_review_score?: number
  total_commits: number
  code_growth_rate: number
  code_reduction_rate: number
  avg_additions_per_mr: number
  avg_deletions_per_mr: number
  productivity_score: number
}

export interface CodeQualityTrend {
  date: string
  avg_score?: number
  review_count: number
  pass_rate: number
}

export interface EfficiencyMetrics {
  avg_mr_duration: number
  avg_review_time: number
  mrs_per_day: number
  commits_per_day: number
}

export interface TechnicalDebt {
  long_pending_mrs: number
  re_reviewed_mrs: number
  high_risk_patterns: number
  oldest_pending_days?: number
}

export interface TokenUsageTrend {
  date: string
  total_tokens: number
  direct_tokens: number
  cache_tokens: number
  prompt_tokens: number
  completion_tokens: number
  cost: number
}

export interface TokenUsageByModel {
  model_name: string
  total_tokens: number
  direct_tokens: number
  cache_tokens: number
  cost: number
  usage_count: number
}

export interface TokenUsageByProject {
  project_name: string
  total_tokens: number
  direct_tokens: number
  cache_tokens: number
  cost: number
  review_count: number
}

export interface StatisticsResponse {
  time_range: TimeRangeFilter
  project_stats: ProjectStats[]
  user_stats: UserStats[]
  quality_trends: CodeQualityTrend[]
  efficiency_metrics: EfficiencyMetrics
  technical_debt: TechnicalDebt
  token_usage_trends: TokenUsageTrend[]
  token_usage_by_model: TokenUsageByModel[]
  token_usage_by_project: TokenUsageByProject[]
  summary: {
    total_projects: number
    total_mrs: number
    total_reviewed: number
    review_coverage: number
    avg_review_score: number
    total_authors: number
    period_days: number
    total_tokens: number
    total_direct_tokens: number
    total_cache_tokens: number
    total_cost: number
  }
}

// 基础统计API
export const basicStatsApi = {
  async getSummary() {
    const response = await api({
      method: 'GET',
      url: '/basic-stats/summary'
    })
    return response
  }
}

// Token统计API
export const tokenStatsApi = {
  async getSummary(days: number = 30) {
    const response = await api({
      method: 'GET',
      url: '/token-stats/summary',
      params: { days }
    })
    return response
  },

  async getTrends(days: number = 30) {
    const response = await api({
      method: 'GET',
      url: '/token-stats/trends',
      params: { days }
    })
    return response
  },

  async getByModel(days: number = 30) {
    const response = await api({
      method: 'GET',
      url: '/token-stats/by-model',
      params: { days }
    })
    return response
  },

  async getByProject(days: number = 30) {
    const response = await api({
      method: 'GET',
      url: '/token-stats/by-project',
      params: { days }
    })
    return response
  }
}

// 项目统计API
export const projectStatsApi = {
  async getStatistics(params: {
    period?: string
    project_ids?: string
    authors?: string
    time_criteria?: string
  } = {}) {
    const response = await api({
      method: 'GET',
      url: '/project-stats/',
      params
    })
    return response
  }
}

// 用户统计API
export const userStatsApi = {
  async getStatistics(params: {
    period?: string
    project_ids?: string
    authors?: string
    time_criteria?: string
  } = {}) {
    const response = await api({
      method: 'GET',
      url: '/user-stats/',
      params
    })
    return response
  }
}

// 质量统计API
export const qualityStatsApi = {
  async getTrends(params: {
    period?: string
    project_ids?: string
    authors?: string
    time_criteria?: string
  } = {}) {
    const response = await api({
      method: 'GET',
      url: '/quality-stats/trends',
      params
    })
    return response
  },

  async getTechnicalDebt(params: {
    period?: string
    project_ids?: string
    authors?: string
    time_criteria?: string
  } = {}) {
    const response = await api({
      method: 'GET',
      url: '/quality-stats/technical-debt',
      params
    })
    return response
  }
}

// 效率统计API
export const efficiencyStatsApi = {
  async getMetrics(params: {
    period?: string
    project_ids?: string
    authors?: string
    time_criteria?: string
  } = {}) {
    const response = await api({
      method: 'GET',
      url: '/efficiency-stats/',
      params
    })
    return response
  }
}

// 组合统计API - 一次性获取所有数据
export const combinedStatsApi = {
  async getAllStatistics(params: {
    period?: string
    project_ids?: string
    authors?: string
    time_criteria?: string
    days?: number
  } = {}) {
    const { period = 'this_month', project_ids, authors, time_criteria = 'activity', days = 30 } = params
    
    const commonParams = { period, project_ids, authors, time_criteria }
    
    // 并行请求所有接口
    const [
      basicSummary,
      tokenSummary,
      tokenTrends,
      tokenByModel,
      tokenByProject,
      projectStats,
      userStats,
      qualityTrends,
      technicalDebt,
      efficiencyMetrics
    ] = await Promise.all([
      basicStatsApi.getSummary(),
      tokenStatsApi.getSummary(days),
      tokenStatsApi.getTrends(days),
      tokenStatsApi.getByModel(days),
      tokenStatsApi.getByProject(days),
      projectStatsApi.getStatistics(commonParams),
      userStatsApi.getStatistics(commonParams),
      qualityStatsApi.getTrends(commonParams),
      qualityStatsApi.getTechnicalDebt(commonParams),
      efficiencyStatsApi.getMetrics(commonParams)
    ])

    // 组合返回数据，保持与原接口兼容的格式
    return {
      time_range: { period, start_date: null, end_date: null },
      project_stats: projectStats,
      user_stats: userStats,
      quality_trends: qualityTrends,
      efficiency_metrics: efficiencyMetrics,
      technical_debt: technicalDebt,
      token_usage_trends: tokenTrends,
      token_usage_by_model: tokenByModel,
      token_usage_by_project: tokenByProject,
      summary: {
        total_projects: basicSummary.total_projects,
        total_mrs: basicSummary.total_merge_requests,
        total_reviewed: basicSummary.reviewed_merge_requests,
        review_coverage: basicSummary.review_coverage,
        avg_review_score: (() => {
          // 从用户统计中计算平均得分
          const usersWithScore = userStats.filter((user: UserStats) => user.avg_review_score && user.avg_review_score > 0)
          if (usersWithScore.length === 0) return 0
          const totalScore = usersWithScore.reduce((sum: number, user: UserStats) => sum + (user.avg_review_score || 0), 0)
          return Math.round(totalScore / usersWithScore.length * 100) / 100 // 保留两位小数
        })(),
        total_authors: userStats.length,
        period_days: days,
        // Token相关汇总
        total_tokens: tokenSummary.total_tokens,
        total_direct_tokens: tokenSummary.total_direct_tokens,
        total_cache_tokens: tokenSummary.total_cache_tokens,
        total_cost: tokenSummary.total_cost
      }
    }
  }
}

export default {
  basicStatsApi,
  tokenStatsApi,
  projectStatsApi,
  userStatsApi,
  qualityStatsApi,
  efficiencyStatsApi,
  combinedStatsApi
}
