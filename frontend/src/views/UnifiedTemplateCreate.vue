<template>
  <div class="unified-template-create">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.back()" :icon="ArrowLeft" class="back-btn">
          返回
        </el-button>
        <h2>创建审查模板</h2>
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

          <!-- 步骤2: 模板内容 (AI创建或手动创建) -->
          <div v-show="currentStep === 1" class="template-content-step">
            <div class="step-header">
              <div class="header-with-switch">
                <el-button 
                  type="primary" 
                  @click="switchCreationMode"
                  class="mode-switch-title-btn"
                >
                  <el-icon><Switch /></el-icon>
                  {{ creationMode === 'ai' ? 'AI智能生成' : '手动编写' }}
                </el-button>
              </div>
            </div>

            <!-- AI创建模式 -->
            <div v-if="creationMode === 'ai'" class="ai-creation-mode">
              <AIGenerationStep
                :form="form"
                @template-generated="onTemplateGenerated"
              />
            </div>

            <!-- 手动创建模式 -->
            <div v-else class="manual-creation-mode">
              <TemplateContentStep
                :form="form"
                @template-change="onTemplateChange"
                @insert-variable="() => insertVariable('')"
              />
            </div>



            <!-- 操作按钮 -->
            <div class="step-actions">
              <el-button @click="prevStep" :icon="ArrowLeft">
                上一步
              </el-button>
              
              <el-button 
                type="primary" 
                @click="nextStep"
                :disabled="!canProceedToNext"
                :icon="ArrowRight"
              >
                下一步
              </el-button>
            </div>
          </div>

          <!-- 步骤3: 模板预览和提交 -->
          <TemplatePreviewStep
            v-show="currentStep === 2"
            :form="form"
            :loading="loading"
            :is-edit="false"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, ArrowRight, Switch, Star, Plus, Refresh, Warning 
} from '@element-plus/icons-vue'
import { 
  createPromptTemplate,
  type PromptTemplateCreate
} from '@/api/prompt'
import { useVariablesStore } from '@/stores/variables'
import StepNavigation from '@/components/prompt/StepNavigation.vue'
import BasicConfigStep from '@/components/prompt/BasicConfigStep.vue'
import AIGenerationStep from '@/components/prompt/AIGenerationStep.vue'
import TemplateContentStep from '@/components/prompt/TemplateContentStep.vue'
import TemplatePreviewStep from '@/components/prompt/TemplatePreviewStep.vue'

// 路由
const router = useRouter()

// 变量存储
const variablesStore = useVariablesStore()

// 响应式数据
const loading = ref(false)
const currentStep = ref(0)
const creationMode = ref<'ai' | 'manual'>('ai') // 默认AI模式
const variableDialogVisible = ref(false)

// 步骤配置
const steps = ref([
  {
    title: '基础配置',
    description: '设置模板基本信息',
    completed: false,
    available: true
  },
  {
    title: '模板内容',
    description: 'AI生成或手动编写',
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

// 表单验证
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

// 是否可以进入下一步
const canProceedToNext = computed(() => {
  return form.template_content && form.template_content.trim().length > 0
})

// 计算属性
const coreVariables = computed(() => {
  return variablesStore.coreVariables
})

const extendedVariables = computed(() => {
  return variablesStore.extendedVariables
})

// 生命周期
onMounted(async () => {
  // 加载变量
  await variablesStore.loadVariables()
})

// 步骤导航
const goToStep = (index: number) => {
  if (steps.value[index]?.available) {
    currentStep.value = index
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
      currentStepValid = true
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
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 创建方式变化处理
const onCreationModeChange = (mode: 'ai' | 'manual') => {
  creationMode.value = mode
  
  // 如果切换到AI模式，清空现有内容
  if (mode === 'ai' && form.template_content) {
    ElMessage.info('切换到AI模式，将清空现有模板内容')
    form.template_content = ''
    form.variables_schema = {}
  }
  
  // 如果切换到手动模式，提示用户
  if (mode === 'manual') {
    ElMessage.info('切换到手动模式，您可以自由编写Jinja2模板')
  }
}

// 切换创建方式
const switchCreationMode = () => {
  const newMode = creationMode.value === 'ai' ? 'manual' : 'ai'
  creationMode.value = newMode
  
  // 清空现有内容
  form.template_content = ''
  form.variables_schema = {}
}

// AI生成模板内容回调
const onTemplateGenerated = (content: string) => {
  form.template_content = content
  
  // 自动设置变量schema
  form.variables_schema = generateVariablesSchema(content)
  
  ElMessage.success('AI模板生成完成！')
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
        const variable = variablesStore.getVariableByName(varName)
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
  console.log('插入变量:', variableName)
  variableDialogVisible.value = false
}

// 选择变量
const selectVariable = (variableName: string) => {
  console.log('选择变量:', variableName)
  variableDialogVisible.value = false
}

// 提交表单
const handleSubmit = async () => {
  try {
    loading.value = true
    
    // 标记当前步骤为完成
    if (currentStep.value === steps.value.length - 1) {
      steps.value[currentStep.value].completed = true
    }
    
    // 创建模板
    await createPromptTemplate(form)
    ElMessage.success('模板创建成功')
    
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
.unified-template-create {
  height: 100%;
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
  padding: 0.3vh 1vw;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
  height: 4vh;
  min-height: 30px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #606266;
  font-size: 12px;
  padding: 4px 8px;
  height: 24px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}

.header-left h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.edit-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.steps-layout {
  display: flex;
  width: 100%;
  height: 100%;
}

.steps-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  margin: 1vh 1vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.template-content-step {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.step-header {
  margin-bottom: 24px;
}

.step-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-with-switch {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 16px;
  margin-left: 4vh; /* 与变量面板宽度对齐 */
}

.mode-switch-title-btn {
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
  height: 36px;
  border-radius: 6px;
  border: 1px solid #8b5cf6;
  color: #8b5cf6;
  background: #faf5ff;
  transition: all 0.2s ease;
  cursor: pointer;
  min-width: 120px;
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.1);
}

.mode-switch-title-btn:hover {
  background: #8b5cf6;
  border-color: #7c3aed;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.25);
}

.mode-switch-title-btn .el-icon {
  margin-right: 6px;
  font-size: 16px;
}

.step-description {
  text-align: left;
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}

.creation-mode-selector {
  margin-bottom: 24px;
  text-align: center;
}

.creation-mode-selector .el-radio-group {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 4px;
}

.creation-mode-selector .el-radio-button__inner {
  border: none;
  background: transparent;
  color: #606266;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.creation-mode-selector .el-radio-button__inner:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.creation-mode-selector .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.creation-mode-selector .el-icon {
  margin-right: 6px;
  font-size: 16px;
}

.ai-creation-mode,
.manual-creation-mode {
  flex: 1;
  margin-bottom: 24px;
}

.mode-switch-tip {
  margin-bottom: 24px;
}

.switch-mode-btn {
  margin-top: 12px;
  font-weight: 500;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  margin-top: auto;
}

.step-actions .el-button {
  min-width: 100px;
}

/* 变量对话框样式 */
.variable-dialog {
  border-radius: 12px;
}

.variable-groups {
  max-height: 400px;
  overflow-y: auto;
}

.variable-group {
  margin-bottom: 24px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  font-weight: 600;
  color: #303133;
}

.group-variables {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-item {
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.variable-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  transform: translateY(-1px);
}

.variable-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.variable-name code {
  background: #f1f3f4;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #303133;
}

.variable-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
}

.variable-example {
  color: #909399;
  font-size: 13px;
  line-height: 1.4;
}

.loading-state,
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: #909399;
  font-size: 14px;
}

.loading-state .el-icon {
  font-size: 18px;
}

.error-state .el-icon {
  color: #f56c6c;
  font-size: 18px;
}

.dialog-footer {
  text-align: right;
}
</style>
