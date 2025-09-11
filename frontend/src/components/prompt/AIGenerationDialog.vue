<template>
  <el-dialog
    v-model="dialogVisible"
    title="AI生成Prompt模板"
    width="800px"
    append-to-body
    class="ai-generation-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div class="generation-form">
      <!-- 基础信息 -->
      <div class="form-section">
        <h4>基础信息</h4>
        <el-form :model="form" label-width="100px" size="default">
          <el-form-item label="模板名称" required>
            <el-input
              v-model="form.template_name"
              placeholder="请输入模板名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="模板描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="请输入模板描述"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 变量选择 -->
      <div class="form-section">
        <h4>选择变量</h4>
        <div class="variables-selection">
          <div class="variables-header">
            <span>选择要使用的变量（可选，不选择则使用所有变量）</span>
            <div class="variables-actions">
              <el-button size="small" @click="selectAllVariables" :icon="Select">
                全选
              </el-button>
              <el-button size="small" @click="clearAllVariables" :icon="Delete">
                清空
              </el-button>
            </div>
          </div>
          
          <div class="variables-groups">
            <!-- 核心变量组 -->
            <div v-if="coreVariables.length > 0" class="variable-group">
              <div class="group-title">
                <el-icon><Star /></el-icon>
                <span>核心变量</span>
              </div>
              <div class="variables-list">
                <el-checkbox
                  v-for="variable in coreVariables"
                  :key="variable.name"
                  v-model="variable.selected"
                >
                  <div class="variable-item">
                    <code>{{ variable.name }}</code>
                    <span class="variable-desc">{{ variable.description }}</span>
                  </div>
                </el-checkbox>
              </div>
            </div>

            <!-- 扩展变量组 -->
            <div v-if="extendedVariables.length > 0" class="variable-group">
              <div class="group-title">
                <el-icon><Setting /></el-icon>
                <span>扩展变量</span>
              </div>
              <div class="variables-list">
                <el-checkbox
                  v-for="variable in extendedVariables"
                  :key="variable.name"
                  v-model="variable.selected"
                >
                  <div class="variable-item">
                    <code>{{ variable.name }}</code>
                    <span class="variable-desc">{{ variable.description }}</span>
                  </div>
                </el-checkbox>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI提示词 -->
      <div class="form-section">
        <h4>AI提示词</h4>
        <div class="ai-prompt-section">
          <div class="prompt-header">
            <span>描述你想要的模板特点和要求</span>
            <div class="prompt-actions">
              <el-button size="small" @click="insertPromptTemplate" :icon="Document">
                插入模板
              </el-button>
              <el-button size="small" @click="clearPrompt" :icon="Delete">
                清空
              </el-button>
            </div>
          </div>
          <el-input
            v-model="form.ai_prompt"
            type="textarea"
            :rows="6"
            placeholder="例如：生成一个专注于安全审查的模板，重点关注SQL注入、XSS攻击、权限控制等安全问题，要求输出包含安全评分和建议..."
            maxlength="2000"
            show-word-limit
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button 
          type="primary" 
          :loading="generating" 
          @click="handleGenerate"
          :disabled="!canGenerate"
        >
          {{ generating ? '生成中...' : '开始生成' }}
        </el-button>
      </div>
    </template>

    <!-- 提示词模板选择对话框 -->
    <el-dialog
      v-model="promptTemplateDialogVisible"
      title="选择提示词模板"
      width="600px"
      append-to-body
      class="prompt-template-dialog"
    >
      <div class="prompt-templates">
        <div
          v-for="template in promptTemplates"
          :key="template.id"
          class="prompt-template-item"
          @click="selectPromptTemplate(template)"
        >
          <div class="template-title">{{ template.title }}</div>
          <div class="template-desc">{{ template.description }}</div>
          <div class="template-content">{{ template.content }}</div>
        </div>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Select, Delete, Document, Star, Setting } from '@element-plus/icons-vue'
import { generateAITemplate, type AITemplateGenerationRequest } from '@/api/prompt'
import { useVariablesStore } from '@/stores/variables'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'generated', template: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 变量store
const variablesStore = useVariablesStore()

// 响应式数据
const generating = ref(false)
const promptTemplateDialogVisible = ref(false)

// 表单数据
const form = reactive({
  template_name: '',
  description: '',
  ai_prompt: ''
})

// 提示词模板
const promptTemplates = ref([
  {
    id: 1,
    title: '安全审查模板',
    description: '专注于安全漏洞检测',
    content: '生成一个专注于安全审查的模板，重点关注SQL注入、XSS攻击、权限控制、输入验证等安全问题。要求输出包含安全评分、风险等级、具体漏洞描述和修复建议。'
  },
  {
    id: 2,
    title: '性能优化模板',
    description: '专注于性能问题检测',
    content: '生成一个专注于性能优化的模板，重点关注算法复杂度、内存使用、数据库查询优化、缓存策略等性能问题。要求输出包含性能评分、瓶颈分析、优化建议。'
  },
  {
    id: 3,
    title: '代码质量模板',
    description: '专注于代码质量评估',
    content: '生成一个专注于代码质量的模板，重点关注代码可读性、可维护性、代码规范、设计模式使用等。要求输出包含质量评分、改进建议、最佳实践推荐。'
  },
  {
    id: 4,
    title: '测试覆盖模板',
    description: '专注于测试完整性评估',
    content: '生成一个专注于测试覆盖的模板，重点关注单元测试、集成测试、边界条件测试、异常处理测试等。要求输出包含测试评分、测试建议、覆盖率分析。'
  }
])

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const canGenerate = computed(() => {
  return form.template_name.trim() && form.ai_prompt.trim()
})

// 变量分组
const coreVariables = computed(() => {
  return variablesStore.variables
    .filter(v => v.group === 'core')
    .map(v => ({ ...v, selected: false }))
})

const extendedVariables = computed(() => {
  return variablesStore.variables
    .filter(v => v.group === 'extended')
    .map(v => ({ ...v, selected: false }))
})

// 方法
const selectAllVariables = () => {
  coreVariables.value.forEach(v => v.selected = true)
  extendedVariables.value.forEach(v => v.selected = true)
}

const clearAllVariables = () => {
  coreVariables.value.forEach(v => v.selected = false)
  extendedVariables.value.forEach(v => v.selected = false)
}

const insertPromptTemplate = () => {
  promptTemplateDialogVisible.value = true
}

const selectPromptTemplate = (template: any) => {
  form.ai_prompt = template.content
  promptTemplateDialogVisible.value = false
  ElMessage.success(`已插入提示词模板: ${template.title}`)
}

const clearPrompt = () => {
  form.ai_prompt = ''
}

const handleCancel = () => {
  dialogVisible.value = false
  resetForm()
}

const handleGenerate = async () => {
  try {
    generating.value = true
    
    // 获取选中的变量
    const selectedVariables = [
      ...coreVariables.value.filter(v => v.selected).map(v => v.name),
      ...extendedVariables.value.filter(v => v.selected).map(v => v.name)
    ]
    
    // 构建请求数据
    const requestData: AITemplateGenerationRequest = {
      template_name: form.template_name,
      description: form.description,
      variables: selectedVariables,
      ai_prompt: form.ai_prompt
    }
    
    // 调用AI生成API
    const response = await generateAITemplate(requestData)
    
    ElMessage.success(`模板生成成功！使用了 ${response.tokens_used} 个token`)
    
    // 触发生成成功事件
    emit('generated', response.data)
    
    // 关闭对话框
    dialogVisible.value = false
    resetForm()
    
  } catch (error: any) {
    console.error('AI生成失败:', error)
    ElMessage.error(error.response?.data?.detail || 'AI生成失败，请重试')
  } finally {
    generating.value = false
  }
}

const resetForm = () => {
  form.template_name = ''
  form.description = ''
  form.ai_prompt = ''
}

// 监听对话框打开，加载变量
watch(dialogVisible, async (newVal) => {
  if (newVal) {
    try {
      await variablesStore.fetchVariables()
    } catch (error) {
      console.error('加载变量失败:', error)
    }
  }
})
</script>

<style scoped>
.ai-generation-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.ai-generation-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
}

.ai-generation-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 18px;
}

.ai-generation-dialog :deep(.el-dialog__body) {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.generation-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
}

.form-section h4 {
  margin: 0 0 16px 0;
  color: #343a40;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.variables-selection {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.variables-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6c757d;
  font-size: 14px;
}

.variables-actions {
  display: flex;
  gap: 8px;
}

.variables-groups {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.variable-group {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #495057;
  font-weight: 600;
  font-size: 14px;
}

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.variable-item code {
  background: #e9ecef;
  color: #495057;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.variable-desc {
  color: #6c757d;
  font-size: 12px;
}

.ai-prompt-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6c757d;
  font-size: 14px;
}

.prompt-actions {
  display: flex;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 提示词模板对话框样式 */
.prompt-template-dialog :deep(.el-dialog) {
  border-radius: 12px;
}

.prompt-templates {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.prompt-template-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.prompt-template-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.template-title {
  font-weight: 600;
  color: #343a40;
  margin-bottom: 8px;
  font-size: 14px;
}

.template-desc {
  color: #6c757d;
  font-size: 12px;
  margin-bottom: 8px;
}

.template-content {
  color: #495057;
  font-size: 13px;
  line-height: 1.5;
  background: white;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-generation-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 20px auto;
  }
  
  .variables-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .prompt-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
