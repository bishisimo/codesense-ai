<template>
  <el-dialog
    v-model="visible"
    title="⚙️ 自定义审查"
    width="600px"
    :before-close="handleClose"
    class="custom-review-dialog"
  >
    <div class="custom-review-form">
      <!-- 审查模板选择 -->
      <div class="form-section">
        <div class="section-header">
          <div class="section-icon">📋</div>
          <div class="section-title">
            <h4>审查模板</h4>
            <p class="section-desc">选择适合的审查模板</p>
          </div>
        </div>
        <el-select
          v-model="selectedTemplateId"
          style="width: 100%"
          :loading="templatesLoading"
          size="large"
          class="template-select"
        >
          <el-option
            v-for="template in templates"
            :key="template.id"
            :label="template.name"
            :value="template.id"
          >
            <div class="template-option">
              <span class="template-name">{{ template.name }}</span>
              <span class="template-desc">{{ template.description }}</span>
            </div>
          </el-option>
        </el-select>
      </div>

      <!-- 自定义审查说明 -->
      <div class="form-section">
        <div class="section-header">
          <div class="section-icon">✏️</div>
          <div class="section-title">
            <h4>自定义审查说明</h4>
            <p class="section-desc">添加特殊的审查要求或说明</p>
          </div>
        </div>
        <el-input
          v-model="customInstructions"
          type="textarea"
          :rows="5"
          maxlength="500"
          show-word-limit
          class="custom-instructions"
          resize="none"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button size="large" @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          size="large"
          @click="handleConfirm"
          :loading="confirmLoading"
          :disabled="!selectedTemplateId"
          class="confirm-button"
        >
          <el-icon v-if="!confirmLoading"><Check /></el-icon>
          {{ confirmLoading ? '审查中...' : '开始审查' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'

interface ReviewTemplate {
  id: number
  name: string
  description: string
  is_active: boolean
}

interface Props {
  modelValue: boolean
  mrId: number
  mrTitle: string
  isReviewing: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', options: {
    force: boolean
    template_id?: number
    custom_instructions?: string
  }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)
const selectedTemplateId = ref<number>()
const customInstructions = ref('')
const templates = ref<ReviewTemplate[]>([])
const templatesLoading = ref(false)
const confirmLoading = ref(false)

// 监听modelValue变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    loadTemplates()
  }
})

// 监听visible变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

const loadTemplates = async () => {
  try {
    templatesLoading.value = true
    const response = await adminApi.getReviewTemplates()
    templates.value = response.items
    
    // 设置默认模板（第一个模板或名为"默认"的模板）
    if (templates.value.length > 0) {
      const defaultTemplate = templates.value.find(t => t.name.includes('默认') || t.name.includes('Default'))
      selectedTemplateId.value = defaultTemplate ? defaultTemplate.id : templates.value[0].id
    }
  } catch (error) {
    console.error('加载审查模板失败:', error)
    ElMessage.error('加载审查模板失败')
  } finally {
    templatesLoading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  // 重置表单
  selectedTemplateId.value = undefined
  customInstructions.value = ''
}

const handleConfirm = async () => {
  try {
    confirmLoading.value = true
    
    const options: {
      force: boolean
      template_id?: number
      custom_instructions?: string
    } = {
      force: props.isReviewing // 如果正在审查中，则使用force
    }

    options.template_id = selectedTemplateId.value
    options.custom_instructions = customInstructions.value

    emit('confirm', options)
    handleClose()
  } catch (error) {
    console.error('确认审查失败:', error)
  } finally {
    confirmLoading.value = false
  }
}
</script>

<style scoped>
.custom-review-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  border-radius: 8px 8px 0 0;
}

.custom-review-dialog :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.custom-review-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.custom-review-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.custom-review-form {
  padding: 0;
}

.form-section {
  margin-bottom: 32px;
  background: #fafbfc;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e8eaed;
  transition: all 0.3s ease;
}

.form-section:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 24px;
  margin-top: 2px;
}

.section-title h4 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.section-desc {
  margin: 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.4;
}

.template-select {
  border-radius: 8px;
}

.template-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.template-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.template-select :deep(.el-select-dropdown) {
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e8eaed;
  max-height: 300px;
  overflow-y: auto;
}

.template-select :deep(.el-select-dropdown__list) {
  padding: 8px 0;
}

.template-select :deep(.el-select-dropdown__item) {
  padding: 8px 16px;
  height: 32px;
  line-height: 32px;
  border-radius: 4px;
  margin: 2px 8px;
  transition: all 0.2s ease;
}

.template-select :deep(.el-select-dropdown__item:hover) {
  background-color: #f0f9ff;
  color: #409eff;
}

.template-select :deep(.el-select-dropdown__item.is-selected) {
  background-color: #e6f7ff;
  color: #409eff;
  font-weight: 500;
}

.template-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.template-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.template-desc {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
}

.custom-instructions :deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-size: 14px;
  line-height: 1.6;
}

.custom-instructions :deep(.el-textarea__inner:hover) {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.custom-instructions :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 20px 24px;
  background: #f8f9fa;
  border-radius: 0 0 8px 8px;
  margin: 0 -24px -24px -24px;
}

.confirm-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.confirm-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.confirm-button:disabled {
  background: #c0c4cc;
  transform: none;
  box-shadow: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .custom-review-dialog {
    width: 95% !important;
    margin: 0 auto;
  }
  
  .form-section {
    padding: 16px;
    margin-bottom: 24px;
  }
  
  .section-header {
    gap: 8px;
  }
  
  .section-icon {
    font-size: 20px;
  }
}
</style>
