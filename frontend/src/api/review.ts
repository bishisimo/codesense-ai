import request from './index'

export interface ReviewComment {
  id: number
  review_id: number
  file_path?: string
  line_number?: number
  comment_type: string
  content: string
  created_at: string
}

export interface CodeReview {
  id: number
  merge_request_id: number
  commit_sha: string
  score?: number
  level?: string
  summary?: string
  categories?: ReviewCategory[]
  issues?: ReviewIssue[]
  review_content?: string
  reviewer_type: string
  status: string
  created_at: string
  updated_at: string
  comments: ReviewComment[]
}

export interface ReviewCategory {
  name: string
  score: number
  level: string
  description: string
}

export interface ReviewIssue {
  id: string
  type: string
  severity: string
  category: string
  title: string
  description: string
  file?: string
  line?: number | null
  suggestion?: string
}

export interface ReviewContent {
  review_id: number
  content: string
}

// 注意：ReviewTaskResponse、TaskStatus、ReviewResult 类型定义已移至 admin.ts 中，避免重复定义

export const reviewApi = {
  // 获取代码审查详情
  getReview: (reviewId: number): Promise<CodeReview> => {
    return request({
      url: `/reviews/${reviewId}`,
      method: 'GET'
    })
  },

  // 获取审查内容
  getReviewContent: (reviewId: number): Promise<ReviewContent> => {
    return request({
      url: `/reviews/${reviewId}/content`,
      method: 'GET'
    })
  },

  // 注意：审查任务相关的API已移至adminApi中，避免重复定义
}
