<template>
  <div class="review-detail-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-page-header @back="goBack" class="back-header">
        <template #content>
          <div class="header-content">
            <!-- 版本选择器 -->
            <div class="version-selector">
              <el-icon class="version-icon"><Share /></el-icon>
              <span class="version-label">版本选择</span>
              <el-select
                v-model="selectedReviewId"
                :placeholder="reviewHistory.length === 1 ? '当前版本' : '选择要查看的审查版本'"
                @change="handleReviewChange"
                class="version-select"
                :class="{ 'single-version': reviewHistory.length === 1 }"
                popper-class="version-select-dropdown"
                :disabled="reviewHistory.length === 1"
              >
                <el-option
                  v-for="review in reviewHistory"
                  :key="review.id"
                  :label="getCommitOptionLabel(review)"
                  :value="review.id"
                  :disabled="review.is_reviewing"
                  :class="[
                    'version-option',
                    { 'selected': review.id === selectedReviewId },
                    { 'latest': review.is_latest && !review.is_reviewing },
                    { 'reviewing': review.is_reviewing }
                  ]"
                >
                  <div class="version-option-content">
                    <div class="version-main-info">
                      <div class="version-sha">
                        <el-icon class="version-icon"><Document /></el-icon>
                        <span class="sha-text">{{ review.commit_sha_short }}</span>
                      </div>
                      <div class="version-meta">
                        <span class="version-date">
                          <el-icon class="date-icon"><Clock /></el-icon>
                          {{ formatDate(review.created_at) }}
                        </span>
                      </div>
                    </div>
                    <div class="version-status">
                      <el-tag 
                        v-if="review.is_reviewing" 
                        type="warning" 
                        size="small" 
                        class="status-tag"
                        effect="dark"
                      >
                        <el-icon><Loading /></el-icon>
                        审查中
                      </el-tag>
                      <el-tag 
                        v-else-if="review.is_latest" 
                        type="success" 
                        size="small" 
                        class="status-tag"
                        effect="dark"
                      >
                        <el-icon><Star /></el-icon>
                        最新
                      </el-tag>
                      <el-tag 
                        v-if="review.score !== null && review.score !== undefined && !review.is_reviewing" 
                        :type="getScoreType(review.score)" 
                        size="small" 
                        class="score-tag"
                        effect="dark"
                      >
                        {{ review.score }}分
                      </el-tag>
                    </div>
                  </div>
                </el-option>
              </el-select>
            </div>
          </div>
        </template>
      </el-page-header>
    </div>
    
    <!-- 共享的审查报告内容组件 -->
    <ReviewReportContent
      :review-data="reviewData"
      :review-history="reviewHistory"
      :selected-review-id="selectedReviewId"
      @update:selected-review-id="handleReviewChange"
      @review-change="handleReviewChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Share,
  Document,
  Clock,
  Star,
  Check,
  Loading
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { reviewApi, type CodeReview } from '@/api/review'
import { adminApi, type ReviewHistoryItem } from '@/api/admin'
import ReviewReportContent from '@/components/ReviewReportContent.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const reviewHistory = ref<ReviewHistoryItem[]>([])
const selectedReviewId = ref<number | undefined>()
const historyLoading = ref(false)
const reviewData = ref<CodeReview>({
  id: 0,
  merge_request_id: 0,
  commit_sha: '',
  score: undefined,
  review_content: '',
  reviewer_type: '',
  status: '',
  created_at: '',
  updated_at: '',
  comments: []
})

// 调试信息已移除，避免生产环境中的调试输出



const loadReviewData = async () => {
  try {
    loading.value = true
    const reviewId = Number(route.params.id)
    reviewData.value = await reviewApi.getReview(reviewId)
    
    // 设置当前选中的review ID
    selectedReviewId.value = reviewData.value.id
    console.log('设置selectedReviewId为:', selectedReviewId.value, '类型:', typeof selectedReviewId.value)
    
    // 加载review历史
    await loadReviewHistory()
  } catch (error) {
    ElMessage.error('加载审查详情失败')
  } finally {
    loading.value = false
  }
}

const loadReviewHistory = async () => {
  if (!reviewData.value.merge_request_id) return
  
  try {
    historyLoading.value = true
    const response = await adminApi.getMergeRequestReviews(reviewData.value.merge_request_id)
    reviewHistory.value = response.reviews
    
    // 只有在selectedReviewId还没有设置的情况下才设置默认值
    if (!selectedReviewId.value) {
      selectedReviewId.value = reviewData.value.id
    }
    
    // 初始化选择逻辑，确保选择非审查中的版本
    initializeSelection()
  } catch (err: any) {
    console.error('加载review历史失败:', err)
    ElMessage.error('加载review历史失败')
  } finally {
    historyLoading.value = false
  }
}

const handleReviewChange = async (reviewId: number) => {
  if (!reviewId) return
  
  console.log('handleReviewChange被调用，reviewId:', reviewId, '类型:', typeof reviewId)
  
  try {
    loading.value = true
    // selectedReviewId 会通过 v-model 自动更新
    reviewData.value = await reviewApi.getReview(reviewId)
  } catch (err: any) {
    console.error('切换review失败:', err)
    ElMessage.error('加载审查报告失败')
  } finally {
    loading.value = false
  }
}

// 获取非审查中的最新版本
const getLatestNonReviewingReview = () => {
  return reviewHistory.value.find(review => review.is_latest && !review.is_reviewing)
}

// 初始化选择逻辑
const initializeSelection = () => {
  if (reviewHistory.value.length === 0) return
  
  // 优先选择当前选中的版本（如果存在且不在审查中）
  const currentReview = reviewHistory.value.find(r => r.id === selectedReviewId.value)
  if (currentReview && !currentReview.is_reviewing) {
    return
  }
  
  // 否则选择非审查中的最新版本
  const latestNonReviewing = getLatestNonReviewingReview()
  if (latestNonReviewing) {
    selectedReviewId.value = latestNonReviewing.id
  } else {
    // 如果所有版本都在审查中，选择第一个非审查中的版本
    const firstNonReviewing = reviewHistory.value.find(r => !r.is_reviewing)
    if (firstNonReviewing) {
      selectedReviewId.value = firstNonReviewing.id
    }
  }
}



const goBack = () => {
  // 检查是否有保存的分页状态，如果有则返回到MR列表页面
  const savedState = localStorage.getItem('mergeRequestsPaginationState')
  if (savedState) {
    router.push('/admin/merge-requests')
  } else {
    router.go(-1)
  }
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

const getScoreType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}



const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

onMounted(() => {
  loadReviewData()
})
</script>

<style scoped>
.review-detail-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}



.commit-option {
  padding: 12px 16px;
  transition: all 0.2s ease;
  line-height: 1.4;
  min-height: 48px;
}

.commit-option:hover {
  background: linear-gradient(135deg, #f5f7fa 0%, #e3f2fd 100%);
}

.commit-option-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 24px;
}

.commit-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.commit-sha {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.2;
  font-family: 'Courier New', monospace;
}

.commit-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.commit-date {
  color: #909399;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
}

.commit-score {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  color: white;
}

.commit-score.score-excellent {
  background: #10b981;
}

.commit-score.score-good {
  background: #f59e0b;
}

.commit-score.score-poor {
  background: #ef4444;
}

.commit-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
}

.page-header {
  margin-bottom: 24px;
}

.back-header {
  background: white;
  border-radius: 8px;
  padding: 16px 20px;
  border: 1px solid #e4e7ed;
  position: relative;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.version-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.version-icon {
  color: #409eff;
  font-size: 16px;
  flex-shrink: 0;
}

.version-label {
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
}

.version-select {
  min-width: 280px;
}

.version-select :deep(.el-input__wrapper) {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  height: 36px;
  transition: all 0.3s ease;
}

.version-select :deep(.el-input__wrapper:hover) {
  border-color: #409eff;
}

.version-select :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

/* 单个版本时的样式 */
.version-select.single-version :deep(.el-input__wrapper) {
  background: #f0f9ff;
  border-color: #bae6fd;
  color: #0369a1;
}

.version-select.single-version :deep(.el-input__wrapper:hover) {
  border-color: #7dd3fc;
}

.version-select.single-version :deep(.el-input__wrapper.is-focus) {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

.version-select.single-version :deep(.el-input__inner) {
  color: #0369a1;
  font-weight: 500;
}

.version-option {
  padding: 12px 16px;
  transition: all 0.2s ease;
  line-height: 1.4;
  min-height: 48px;
}

.version-option:hover {
  background: linear-gradient(135deg, #f5f7fa 0%, #e3f2fd 100%);
}

.version-option.selected {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-left: 3px solid #409eff;
}

.version-option.latest {
  border-left: 3px solid #10b981;
}

.version-option-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 24px;
}

.version-main-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.version-sha {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.2;
  font-family: 'Courier New', monospace;
}

.version-icon {
  color: #409eff;
  font-size: 14px;
}

.sha-text {
  font-weight: 600;
}

.version-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-date {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
}

.date-icon {
  color: #909399;
  font-size: 12px;
}

.version-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-left: 8px;
}

.status-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.score-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  min-width: 40px;
  text-align: center;
}

/* 审查中版本的样式 */
.version-option.reviewing {
  opacity: 0.6;
  cursor: not-allowed;
}

.version-option.reviewing .version-option-content {
  opacity: 0.6;
}

/* 禁用状态的样式 */
:deep(.el-select-dropdown__item.is-disabled) {
  opacity: 0.6;
  cursor: not-allowed;
}

:deep(.el-select-dropdown__item.is-disabled:hover) {
  background: transparent;
}













:deep(.el-page-header__header) {
  padding: 0;
}

:deep(.el-page-header__content) {
  font-size: inherit;
}
</style>
