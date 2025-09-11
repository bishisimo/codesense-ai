<template>
  <div class="review-report-content">

    <!-- 功能描述部分已移除，相关信息已整合到审查总结中 -->
    
    <!-- 审查内容 -->
    <el-card class="content-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Edit /></el-icon>
            审查内容
          </span>
        </div>
      </template>
      
      <div v-if="reviewData.review_content" class="review-content">
        <div class="markdown-content" v-html="renderedContent"></div>
      </div>
      <div v-else class="empty-content">
        <el-empty description="暂无审查内容" />
      </div>
    </el-card>
    
    <!-- 评论列表 -->
    <el-card v-if="reviewData.comments && reviewData.comments.length > 0" 
             class="comments-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><ChatDotRound /></el-icon>
            审查评论 ({{ reviewData.comments.length }})
          </span>
        </div>
      </template>
      
      <div class="comments-list">
        <div v-for="comment in reviewData.comments" 
             :key="comment.id" 
             class="comment-item">
          <div class="comment-header">
            <div class="comment-meta">
              <el-tag :type="getCommentType(comment.comment_type)" size="small" class="comment-type">
                {{ getCommentTypeText(comment.comment_type) }}
              </el-tag>
              <span v-if="comment.file_path" class="file-path">
                <el-icon><Document /></el-icon>
                {{ comment.file_path }}
                <span v-if="comment.line_number" class="line-number">:{{ comment.line_number }}</span>
              </span>
            </div>
            <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
          </div>
          <div class="comment-content">
            {{ comment.content }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  Document, 
  Edit, 
  ChatDotRound,
  Share,
  Clock,
  Star,
  Check,
  Loading
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'
import { type CodeReview } from '@/api/review'
import { type ReviewHistoryItem } from '@/api/admin'

// 定义组件名称
defineOptions({
  name: 'ReviewReportContent'
})

interface Props {
  reviewData: CodeReview
  reviewHistory: ReviewHistoryItem[]
  selectedReviewId: number | undefined
}

interface Emits {
  (e: 'update:selectedReviewId', value: number): void
  (e: 'reviewChange', value: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const md = new MarkdownIt()




const renderedContent = computed(() => {
  if (!props.reviewData.review_content) return ''
  return md.render(props.reviewData.review_content)
})

// describe字段已移除，相关信息已整合到审查总结中

const handleReviewChange = (reviewId: number) => {
  emit('update:selectedReviewId', reviewId)
  emit('reviewChange', reviewId)
}

const getCommitOptionLabel = (review: ReviewHistoryItem) => {
  return review.commit_sha_short
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '进行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getCommentType = (type: string) => {
  const types: Record<string, string> = {
    error: 'danger',
    warning: 'warning',
    suggestion: 'primary',
    info: 'info',
    security: 'danger',
    code_quality: 'warning'
  }
  return types[type] || 'info'
}

const getCommentTypeText = (type: string) => {
  const texts: Record<string, string> = {
    error: '错误',
    warning: '警告',
    suggestion: '建议',
    info: '信息',
    security: '安全',
    code_quality: '代码质量'
  }
  return texts[type] || type
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}
</script>

<style scoped>
.review-report-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}



.commit-option-modern {
  padding: 16px 20px;
  transition: all 0.3s ease;
  line-height: 1.4;
  min-height: 70px;
  display: flex;
  align-items: center;
  border-radius: 8px;
  margin: 4px 0;
}

.commit-option-modern:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.commit-option-content-modern {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 32px;
  gap: 16px;
}

.commit-main-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.commit-sha-modern {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.commit-icon {
  color: #3b82f6;
  font-size: 16px;
}

.sha-text {
  font-weight: 600;
  color: #1e293b;
  font-size: 15px;
  line-height: 1.3;
  font-family: 'Courier New', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.commit-meta-modern {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.commit-date-modern {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.3;
}

.date-icon {
  font-size: 12px;
}

.commit-status-modern {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-tag-modern {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 下拉菜单样式 */
:deep(.commit-select-dropdown) {
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

:deep(.commit-select-dropdown .el-select-dropdown__item) {
  padding: 0;
  height: auto;
}

:deep(.commit-select-dropdown .el-select-dropdown__item:hover) {
  background: transparent;
}

:deep(.commit-select-dropdown .el-select-dropdown__item.selected) {
  background: transparent;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .commit-selector-modern {
    padding: 16px;
    margin-bottom: 20px;
  }
  
  .selector-title {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .title-text {
    font-size: 15px;
  }
  
  .version-count {
    font-size: 13px;
  }
  
  .commit-select-modern {
    max-width: 100%;
  }
  
  .commit-option-modern {
    padding: 12px 16px;
    min-height: 60px;
  }
  
  .commit-option-content-modern {
    gap: 12px;
  }
  
  .sha-text {
    font-size: 14px;
  }
  
  .status-tag-modern {
    font-size: 10px;
    padding: 3px 6px;
  }
}

/* 动画效果 */
.commit-selector-modern {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 选中状态的特殊样式 */
.commit-option-modern.selected {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #3b82f6;
}

/* 最新版本的突出显示 */
.commit-option-modern.latest {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 1px solid #22c55e;
}

.commit-option-modern.latest:hover {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(34, 197, 94, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.describe-content {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.describe-content .markdown-content {
  font-size: 14px;
  line-height: 1.8;
}

.describe-content .markdown-content ul {
  margin: 12px 0;
  padding-left: 20px;
}

.describe-content .markdown-content li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

.review-content {
  color: #303133;
  min-height: 580px;
  padding: 24px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.empty-content {
  text-align: center;
  padding: 40px 0;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.comment-type {
  flex-shrink: 0;
}

.file-path {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #606266;
  font-size: 13px;
  font-family: 'Courier New', monospace;
}

.line-number {
  color: #409eff;
  font-weight: 600;
}

.comment-time {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.comment-content {
  color: #303133;
  line-height: 1.6;
  font-size: 14px;
}

:deep(.markdown-content) {
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

:deep(.markdown-content h1),
:deep(.markdown-content h2),
:deep(.markdown-content h3),
:deep(.markdown-content h4),
:deep(.markdown-content h5),
:deep(.markdown-content h6) {
  margin-top: 32px;
  margin-bottom: 20px;
  font-weight: 700;
  color: #1e293b;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
}

:deep(.markdown-content h1) { 
  font-size: 28px; 
  margin-top: 0;
  border-bottom: 3px solid #3b82f6;
}
:deep(.markdown-content h2) { 
  font-size: 24px; 
  border-bottom: 2px solid #64748b;
}
:deep(.markdown-content h3) { 
  font-size: 20px; 
  border-bottom: 1px solid #cbd5e1;
}
:deep(.markdown-content h4) { 
  font-size: 18px; 
  border-bottom: 1px solid #e2e8f0;
}
:deep(.markdown-content h5) { 
  font-size: 16px; 
  border-bottom: none;
}
:deep(.markdown-content h6) { 
  font-size: 14px; 
  border-bottom: none;
}

:deep(.markdown-content p) {
  margin-bottom: 16px;
  line-height: 1.8;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  margin-bottom: 16px;
  padding-left: 24px;
}

:deep(.markdown-content li) {
  margin-bottom: 8px;
  line-height: 1.6;
}

:deep(.markdown-content blockquote) {
  margin: 20px 0;
  padding: 16px 20px;
  background: #f8fafc;
  border-left: 4px solid #3b82f6;
  border-radius: 6px;
  font-style: italic;
  color: #475569;
}

:deep(.markdown-content code) {
  background: #f1f5f9;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

:deep(.markdown-content pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 20px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 20px 0;
  border: 1px solid #334155;
}

:deep(.markdown-content pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
  border-radius: 0;
  font-size: 14px;
  line-height: 1.6;
}

:deep(.markdown-content table) {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.markdown-content th),
:deep(.markdown-content td) {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

:deep(.markdown-content th) {
  background: #f8fafc;
  font-weight: 600;
  color: #1e293b;
}

:deep(.markdown-content tr:hover) {
  background: #f8fafc;
}

:deep(.markdown-content strong) {
  font-weight: 700;
  color: #1e293b;
}

:deep(.markdown-content em) {
  font-style: italic;
  color: #475569;
}

:deep(.markdown-content a) {
  color: #3b82f6;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-bottom-color 0.2s ease;
}

:deep(.markdown-content a:hover) {
  border-bottom-color: #3b82f6;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>
