<template>
  <div class="prompt-template-edit">

    
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.back()" :icon="ArrowLeft" class="back-btn">
          返回
        </el-button>
        <h2>{{ isEdit ? '编辑模板' : '新建模板' }}</h2>
      </div>
      <div class="header-actions">
        <el-button @click="handlePreview" :icon="View" class="preview-btn">
          预览
        </el-button>
      </div>
    </div>

    <div class="edit-container">
      <div class="steps-layout">
        <!-- 左侧步骤导航 -->
        <StepNavigation 
          :steps="steps"
          :current-step="currentStep"
          @step-change="goToStep"
        />

        <!-- 右侧内容区域 -->
        <div class="steps-content">
          <!-- 步骤1: 基础配置 -->
          <BasicConfigStep
            v-show="currentStep === 0"
            :form="form"
            @next="nextStep"
            @cancel="$router.back()"
          />

          <!-- 步骤2: 模板内容 -->
          <TemplateContentStep
            v-show="currentStep === 1"
            :form="form"
            @next="nextStep"
            @prev="prevStep"
            @insert-variable="insertVariable"
            @template-change="onTemplateChange"
          />

          <!-- 步骤3: 模板预览和提交 -->
          <TemplatePreviewStep
            v-show="currentStep === 2"
            :form="form"
            :loading="loading"
            :is-edit="isEdit"
            :can-submit="canSubmit"
            @prev="prevStep"
            @submit="handleSubmit"
          />
        </div>
      </div>
    </div>

    <!-- 变量选择对话框 -->
    <el-dialog
      v-model="variableDialogVisible"
      title="选择变量"
      width="700px"
      append-to-body
      class="variable-dialog"
    >
      <div class="variable-groups">
        <!-- 加载状态 -->
        <div v-if="variablesStore.loading" class="loading-state">
          <el-icon class="is-loading"><Refresh /></el-icon>
          <span>正在加载变量...</span>
        </div>
        
        <!-- 错误状态 -->
        <div v-else-if="!variablesStore.loaded && !variablesStore.loading" class="error-state">
          <el-icon><Warning /></el-icon>
          <span>加载变量失败，请重试</span>
        </div>
        
        <!-- 变量内容 -->
        <template v-else>
          <!-- 核心变量组 -->
          <div v-if="coreVariables.length > 0" class="variable-group">
            <div class="group-header">
              <el-icon><Star /></el-icon>
              <span>核心变量</span>
              <el-tag size="small" type="success">推荐</el-tag>
            </div>
            <div class="group-variables">
              <div
                v-for="variable in coreVariables"
                :key="variable.name"
                class="variable-item"
                @click="selectVariable(variable.name)"
              >
                <div class="variable-name">
                  <code>{{ variable.name }}</code>
                  <el-tag size="small" type="info">{{ variable.type }}</el-tag>
                </div>
                <div class="variable-description">{{ variable.description }}</div>
                <div class="variable-example" v-if="variable.example">
                  <strong>示例:</strong> {{ variable.example }}
                </div>
              </div>
            </div>
          </div>

          <!-- 扩展变量组 -->
          <div v-if="extendedVariables.length > 0" class="variable-group">
            <div class="group-header">
              <el-icon><Plus /></el-icon>
              <span>扩展变量</span>
            </div>
            <div class="group-variables">
              <div
                v-for="variable in extendedVariables"
                :key="variable.name"
                class="variable-item"
                @click="selectVariable(variable.name)"
              >
                <div class="variable-name">
                  <code>{{ variable.name }}</code>
                  <el-tag size="small" type="warning">{{ variable.type }}</el-tag>
                </div>
                <div class="variable-description">{{ variable.description }}</div>
                <div class="variable-example" v-if="variable.example">
                  <strong>示例:</strong> {{ variable.example }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="variableDialogVisible = false">取消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <PromptPreviewDialog
      v-model="previewDialogVisible"
      :template="form"
      :variables="variablesStore.variables"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, View, Star, Plus, Refresh, Warning 
} from '@element-plus/icons-vue'
import { 
  createPromptTemplate, 
  updatePromptTemplate,
  getPromptTemplate,
  type PromptTemplateCreate,
  type PromptTemplate
} from '@/api/prompt'
import { useVariablesStore } from '@/stores/variables'
import StepNavigation from '@/components/prompt/StepNavigation.vue'
import BasicConfigStep from '@/components/prompt/BasicConfigStep.vue'
import TemplateContentStep from '@/components/prompt/TemplateContentStep.vue'
import TemplatePreviewStep from '@/components/prompt/TemplatePreviewStep.vue'
import PromptPreviewDialog from '@/components/PromptPreviewDialog.vue'

// 路由
const router = useRouter()
const route = useRoute()

// 变量存储
const variablesStore = useVariablesStore()

// 响应式数据
const loading = ref(false)
const currentStep = ref(0)
const variableDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const isEdit = computed(() => route.params.id !== undefined)

// 步骤配置 - 简化为3个步骤
const steps = ref([
  {
    title: '基础配置',
    description: '设置模板基本信息',
    completed: false,
    available: true
  },
  {
    title: '模板内容',
    description: '编写Jinja2模板',
    completed: false,
    available: false
  },
  {
    title: '预览提交',
    description: '预览模板并提交',
    completed: false,
    available: false
  }
])

// 表单数据
const form = reactive<PromptTemplateCreate>({
  name: '',
  description: '',
  template_content: '',
  variables_schema: [],  // 使用列表格式存储变量名称
  // output_format 字段已移除，由后端统一管理
  is_active: true
})

// 表单验证 - 简化验证逻辑
const formValidation = computed(() => {
  const errors: string[] = []
  
  // 基础配置验证
  if (!form.name || !form.name.trim()) {
    errors.push('模板名称')
  }
  if (!form.description || !form.description.trim()) {
    errors.push('模板描述')
  }
  
  // 模板内容验证
  if (!form.template_content || !form.template_content.trim()) {
    errors.push('模板内容')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
})

// 是否可以提交
const canSubmit = computed(() => {
  return formValidation.value.isValid
})

// 计算属性
const coreVariables = computed(() => {
  return variablesStore.variables.filter(v => v.group === 'core')
})

const extendedVariables = computed(() => {
  return variablesStore.variables.filter(v => v.group !== 'core')
})

// 生命周期
onMounted(async () => {
  try {
    // 加载变量
    await variablesStore.fetchVariables()
    // 如果是编辑模式，加载模板数据
    if (isEdit.value) {
      await loadTemplateData()
    }
  } catch (error) {
    console.error('Error in onMounted:', error)
  }
})

// 加载模板数据
const loadTemplateData = async () => {
  try {
    const templateId = route.params.id as string
    const template = await getPromptTemplate(parseInt(templateId))
    
    // 填充表单数据
    Object.assign(form, {
      name: template.name,
      description: template.description,
      template_content: template.template_content,
      variables_schema: template.variables_schema || [],
      // output_format 字段已移除，由后端统一管理
      is_active: template.is_active
    })
    
    // 标记已完成的步骤
    steps.value[0].completed = true
    steps.value[0].available = true
    steps.value[1].available = true
    steps.value[1].completed = true
    steps.value[2].available = true
    steps.value[2].completed = true
    
    currentStep.value = 2
  } catch (error) {
    console.error('加载模板数据失败:', error)
    ElMessage.error('加载模板数据失败')
  }
}

// 步骤导航
const goToStep = (index: number) => {
  // 仅允许跳转到已开放（available）的步骤
  if (steps.value[index]?.available) {
    currentStep.value = index
    console.log('跳转到步骤:', index)
  }
}

const nextStep = () => {
  // 验证当前步骤是否完成
  let currentStepValid = false
  
  switch (currentStep.value) {
    case 0: // 基础配置
      currentStepValid = form.name.trim() && form.description.trim()
      break
    case 1: // 模板内容
      currentStepValid = form.template_content.trim()
      break
    case 2: // 预览提交
      currentStepValid = true // 预览步骤不需要额外验证
      break
  }
  
  if (!currentStepValid) {
    const stepNames = ['基础配置', '模板内容', '预览提交']
    ElMessage.error(`请完善${stepNames[currentStep.value]}信息`)
    return
  }
  
  // 标记当前步骤为完成
  steps.value[currentStep.value].completed = true
  
  // 如果还有下一步，启用下一步
  if (currentStep.value < steps.value.length - 1) {
    steps.value[currentStep.value + 1].available = true
    currentStep.value++
    console.log('进入下一步:', currentStep.value)
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    console.log('返回上一步:', currentStep.value)
  }
}

// 模板内容变化处理
const onTemplateChange = (content: string) => {
  form.template_content = content
  
  // 自动生成变量schema
  form.variables_schema = generateVariablesSchema(content)
}

// 基于模板内容自动生成变量schema
const generateVariablesSchema = (templateContent: string) => {
  const schema: Record<string, any> = {}
  
  // 从模板内容中提取变量
  const variableMatches = templateContent.match(/\{\{\s*(\w+)\s*\}\}/g)
  if (variableMatches) {
    variableMatches.forEach(match => {
      const varName = match.replace(/\{\{\s*|\s*\}\}/g, '')
      if (varName && !schema[varName]) {
        // 查找变量的详细信息
        const variable = variablesStore.variables.find(v => v.name === varName)
        if (variable) {
          schema[varName] = {
            type: variable.type,
            description: variable.description,
            required: false
          }
        } else {
          schema[varName] = {
            type: "string",
            description: `模板变量: ${varName}`,
            required: false
          }
        }
      }
    })
  }
  
  return schema
}

// 插入变量
const insertVariable = (variableName: string) => {
  // 打开变量选择对话框
  variableDialogVisible.value = true
}

// 选择变量
const selectVariable = (variableName: string) => {
  // 在模板内容中插入变量
  const variableText = `{{ ${variableName} }}`
  
  // 获取当前光标位置或添加到末尾
  const textarea = document.querySelector('.template-textarea textarea') as HTMLTextAreaElement
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const currentContent = form.template_content
    
    // 在光标位置插入变量，如果没有选中文本则直接插入
    const newContent = currentContent.substring(0, start) + variableText + currentContent.substring(end)
    form.template_content = newContent
    
    // 设置光标位置到插入的变量后面
    const newCursorPos = start + variableText.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
    textarea.focus()
  } else {
    // 如果没有找到文本框，直接添加到末尾
    form.template_content += variableText
  }
  
  // 关闭对话框
  variableDialogVisible.value = false
  
  // 触发模板内容变化事件
  onTemplateChange(form.template_content)
}

// 预览模板
const handlePreview = () => {
  if (!form.template_content.trim()) {
    ElMessage.warning('请先编写模板内容')
    return
  }
  previewDialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  try {
    loading.value = true
    
    // 标记当前步骤为完成（如果是最后一个步骤）
    if (currentStep.value === steps.value.length - 1) {
      steps.value[currentStep.value].completed = true
    }
    
    if (isEdit.value) {
      // 更新模板
      const templateId = route.params.id as string
      await updatePromptTemplate(parseInt(templateId), form)
      ElMessage.success('模板更新成功')
    } else {
      // 创建模板
      await createPromptTemplate(form)
      ElMessage.success('模板创建成功')
    }
    
    // 返回列表页面
    router.push('/admin/prompt-templates')
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.prompt-template-edit {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
  min-height: 60px;
  box-sizing: border-box;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: 16px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(102, 126, 234, 0.2);
  color: #667eea;
  font-weight: 600;
  border-radius: 6px;
  padding: 12px 20px;
  font-size: 14px;
  transition: all 0.3s ease;
  min-height: 40px;
  box-sizing: border-box;
}

.back-btn:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.preview-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(103, 194, 58, 0.2);
  color: #67c23a;
  font-weight: 600;
  border-radius: 6px;
  padding: 12px 20px;
  font-size: 14px;
  transition: all 0.3s ease;
  min-height: 40px;
  box-sizing: border-box;
}

.preview-btn:hover {
  background: #67c23a;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.3);
}

.edit-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 20px;
  min-height: 0;
  box-sizing: border-box;
}

.steps-layout {
  display: flex;
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 10px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.2);
  min-height: 0;
  box-sizing: border-box;
}

.steps-content {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  background: white;
  overflow-y: auto;
  min-height: 0;
  box-sizing: border-box;
}

.variable-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.variable-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
}

.variable-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 18px;
}

.variable-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.variable-groups {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.variable-group {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #343a40;
  font-weight: 600;
  font-size: 16px;
}

.group-header .el-icon {
  color: #409eff; /* Primary color for icons */
}

.group-header .el-tag {
  margin-left: 10px;
}

.group-variables {
  display: grid;
  gap: 12px;
  max-height: 300px; /* Adjust as needed */
  overflow-y: auto;
}

.variable-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 20px;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.variable-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.variable-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.variable-name code {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
}

.variable-name .el-tag {
  margin-left: 8px;
}

.variable-description {
  color: #6c757d;
  font-size: 14px;
  line-height: 1.5;
}

.variable-example {
  color: #555;
  font-size: 13px;
  margin-top: 4px;
}

/* 加载、错误和空状态样式 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: #6c757d;
}

.loading-state .el-icon,
.error-state .el-icon,
.empty-state .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #409eff;
}

.error-state .el-icon {
  color: #f56c6c;
}

.empty-state .el-icon {
  color: #909399;
}

.loading-state span,
.error-state span,
.empty-state span {
  font-size: 16px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .edit-container {
    padding: 16px;
  }
  
  .steps-layout {
    flex-direction: column;
  }
  
  .steps-content {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 16px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-left {
    justify-content: center;
  }
  
  .header-actions {
    justify-content: center;
  }
}
</style>
