<template>
  <div class="step-panel">
    <div class="ai-generation-content">
      <!-- 左侧变量区域容器 -->
      <div class="variables-container">
        <div 
          class="variables-panel" 
          :class="{ 'collapsed': isVariablesPanelCollapsed }"
          @mouseenter="expandPanel"
          @mouseleave="collapsePanel"
        >
          <!-- 书卷卷轴装饰 -->
          <div class="scroll-rod left-rod"></div>
          <div class="scroll-rod right-rod"></div>
          
          <!-- 书卷纸张效果 -->
          <div class="scroll-paper">
            <div class="panel-header">
              <div class="header-content">
                <h4>选择变量</h4>
                <p>选择AI生成时要使用的变量</p>
              </div>
              <div class="variables-actions">
                <el-button size="small" @click="clearAllVariables" :icon="Delete">
                  清空
                </el-button>
              </div>
            </div>
            <div class="variables-list">
              <el-checkbox
                v-for="variable in variables"
                :key="variable.name"
                v-model="variable.selected"
                @change="onVariableChange"
              >
                <div class="variable-item">
                  <code>{{ variable.name }}</code>
                  <el-tag :type="variable.group === 'core' ? 'success' : 'warning'" size="small">
                    {{ variable.group === 'core' ? '核心' : '扩展' }}
                  </el-tag>
                  <span class="variable-desc">{{ variable.description }}</span>
                </div>
              </el-checkbox>
            </div>
          </div>
          
          <!-- 展开提示 - 书卷展开图标 -->
          <div class="expand-hint-overlay">
            <div class="scroll-unroll-icon">
              <el-icon class="expand-icon"><ArrowRight /></el-icon>
              <div class="scroll-shadow"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧AI生成区域 -->
      <div class="ai-generation-panel">
        <!-- 上半部：用户输入提示词 -->
        <div class="prompt-input-section">
          <div class="section-header">
            <h4>生成提示词</h4>
            <p>描述您希望AI生成的模板内容和要求</p>
          </div>
          <div class="prompt-input-container">
            <el-input
              v-model="promptInput"
              type="textarea"
              :rows="6"
              placeholder="请详细描述您希望生成的模板内容，例如：
1. 模板的用途和目标
2. 需要包含哪些关键信息
3. 期望的输出格式
4. 特殊的业务逻辑要求
5. 需要使用的变量类型

示例：我需要一个代码审查模板，用于审查Python代码的质量、安全性、性能和可维护性。模板应该包含详细的评分标准、问题描述和改进建议。"
              class="prompt-textarea"
            />
            <div class="prompt-actions">
              <el-button 
                type="primary" 
                @click="generateTemplate" 
                :loading="generating"
                :disabled="!promptInput.trim() || generating"
                class="generate-btn"
              >
                <el-icon><Star /></el-icon>
                {{ generating ? 'AI生成中...' : '生成模板' }}
              </el-button>
              <el-button 
                v-if="generating" 
                type="danger" 
                @click="cancelGeneration"
                class="cancel-btn"
              >
                取消生成
              </el-button>
              <el-button @click="clearPrompt" :disabled="!promptInput.trim()">
                清空
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 下半部：生成结果 -->
        <div class="generation-result-section">
          <div class="section-header">
            <h4>生成结果</h4>
            <p>AI生成的Jinja2模板内容</p>
          </div>
          <div class="result-container">
            <div v-if="!generatedContent && !generating" class="empty-state">
              <el-icon><Document /></el-icon>
              <span>点击"生成模板"按钮开始AI生成</span>
            </div>
            <div v-else-if="generating" class="loading-state">
              <el-icon class="is-loading"><Loading /></el-icon>
              <div class="loading-content">
                <span>{{ taskMessage || 'AI正在生成模板内容...' }}</span>
                <el-progress 
                  v-if="taskProgress > 0" 
                  :percentage="Math.round(taskProgress * 100)" 
                  :show-text="false"
                  class="progress-bar"
                />
                <span v-if="taskProgress > 0" class="progress-text">
                  {{ Math.round(taskProgress * 100) }}%
                </span>
              </div>
            </div>
            <div v-else class="generated-content">
              <!-- 生成状态和操作按钮 -->
              <div class="generation-header">
                <div class="generation-status">
                  <el-tag 
                    :type="generationResult?.success ? 'success' : 'danger'" 
                    size="small"
                  >
                    {{ generationResult?.success ? '验证成功' : '验证失败' }}
                  </el-tag>
                  <span class="generation-message">{{ generationResult?.message }}</span>
                </div>
                <div class="generation-actions">
                  <el-button 
                    v-if="generationResult?.success"
                    type="primary" 
                    size="small"
                    @click="showSaveDialog = true"
                  >
                    保存模板
                  </el-button>
                  <el-button 
                    v-if="!generationResult?.success"
                    type="warning" 
                    size="small"
                    @click="showSaveDialog = true"
                  >
                    手动保存
                  </el-button>
                </div>
              </div>
              
              <!-- 验证错误显示 -->
              <div v-if="generationResult?.validation_errors?.length > 0" class="validation-errors">
                <el-alert
                  title="模板验证失败"
                  type="warning"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    <ul>
                      <li v-for="error in generationResult.validation_errors" :key="error">
                        {{ error }}
                      </li>
                    </ul>
                  </template>
                </el-alert>
              </div>
              
              <JinjaEditor
                :model-value="generatedContent"
                :read-only="false"
                :height="'100%'"
                :placeholder="'AI生成的模板内容将显示在这里'"
                @update:model-value="onContentChange"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 保存模板对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存AI生成的模板"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="saveForm" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input 
            v-model="saveForm.template_name" 
            placeholder="请输入模板名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input
            v-model="saveForm.template_description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="!generationResult?.success" label="验证状态">
          <el-alert
            title="模板验证失败"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>当前模板验证失败，但您可以手动编辑后保存。</p>
              <p>保存后，模板将处于"验证失败"状态，需要手动修复后才能激活使用。</p>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showSaveDialog = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="saveTemplate"
            :loading="saving"
            :disabled="!saveForm.template_name.trim()"
          >
            保存模板
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Document, Delete, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { useVariablesStore } from '@/stores/variables'
import JinjaEditor from '@/components/JinjaEditor.vue'
import { 
  generateAITemplate, 
  getAIGenerationStatus, 
  getAIGenerationResult, 
  cancelAIGeneration,
  saveAIGeneratedTemplate,
  type AITemplateGenerationRequest 
} from '@/api/prompt'

interface FormData {
  template_content: string
}

interface Props {
  form: FormData
}

interface Emits {
  (e: 'next'): void
  (e: 'prev'): void
  (e: 'template-generated', content: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 变量store
const variablesStore = useVariablesStore()

// 响应式数据
const promptInput = ref('')
const generatedContent = ref('')
const generating = ref(false)
const isVariablesPanelCollapsed = ref(true) // 默认折叠
const generationResult = ref<any>(null) // AI生成结果
const showSaveDialog = ref(false) // 保存对话框显示状态
const saving = ref(false) // 保存状态
const saveForm = ref({
  template_name: '',
  template_description: ''
})

// 响应式变量数据
const variables = ref<Array<{ name: string; description: string; group: string; selected: boolean }>>([])

// 获取选中的变量
const selectedVariables = computed(() => variables.value.filter(v => v.selected).map(v => v.name))

// 变量操作方法
const clearAllVariables = () => {
  variables.value.forEach(v => v.selected = false)
}

const onVariableChange = () => {
  // 变量选择变化时的处理逻辑
  console.log('选中的变量:', selectedVariables.value)
}

// 防抖定时器
let expandTimer: number | null = null
let collapseTimer: number | null = null

// 展开变量面板
const expandPanel = () => {
  if (collapseTimer) {
    clearTimeout(collapseTimer)
    collapseTimer = null
  }
  
  if (expandTimer) {
    clearTimeout(expandTimer)
  }
  
  expandTimer = setTimeout(() => {
    isVariablesPanelCollapsed.value = false
    expandTimer = null
  }, 0) // 立即展开，减少延迟
}

// 折叠变量面板
const collapsePanel = () => {
  if (expandTimer) {
    clearTimeout(expandTimer)
    expandTimer = null
  }
  
  if (collapseTimer) {
    clearTimeout(collapseTimer)
  }
  
  collapseTimer = setTimeout(() => {
    isVariablesPanelCollapsed.value = true
    collapseTimer = null
  }, 100) // 减少延迟，快速响应
}

// 任务状态管理
const currentTaskId = ref<string>('')
const taskStatus = ref<string>('')
const taskProgress = ref<number>(0)
const taskMessage = ref<string>('')
const statusPolling = ref<number | null>(null)

// 生成模板
const generateTemplate = async () => {
  if (!promptInput.value.trim()) {
    ElMessage.warning('请输入生成提示词')
    return
  }
  
  if (selectedVariables.value.length === 0) {
    ElMessage.warning('请至少选择一个变量')
    return
  }
  
  generating.value = true
  taskStatus.value = ''
  taskProgress.value = 0
  taskMessage.value = ''

  try {
    // 构建请求数据
    const requestData: AITemplateGenerationRequest = {
      prompt: promptInput.value.trim(),
      selected_variables: selectedVariables.value,
      template_name: undefined,
      description: undefined
    }
    
    // 提交异步任务
    const response = await generateAITemplate(requestData)
    currentTaskId.value = response.task_id
    
    ElMessage.success('AI生成任务已提交，正在处理中...')
    
    // 开始轮询任务状态
    startStatusPolling()
    
  } catch (error: any) {
    console.error('提交AI生成任务失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交AI生成任务失败')
    generating.value = false
  }
}

// 开始状态轮询
const startStatusPolling = () => {
  if (statusPolling.value) {
    clearInterval(statusPolling.value)
  }

  statusPolling.value = setInterval(async () => {
    try {
      const status = await getAIGenerationStatus(currentTaskId.value)
      taskStatus.value = status.status
      taskProgress.value = status.progress
      taskMessage.value = status.message

      if (status.status === 'completed') {
        // 任务完成，获取结果
        const result = await getAIGenerationResult(currentTaskId.value)
        generatedContent.value = result.template_content
        generationResult.value = result
        emit('template-generated', result.template_content)

        if (result.success) {
          ElMessage.success(
            `模板生成并验证成功！使用了 ${result.variables_used?.length || 0} 个变量`
          )
        } else {
          ElMessage.warning(
            `模板生成成功但验证失败，可以手动编辑后保存`
          )
        }
        
        stopStatusPolling()
        generating.value = false
      } else if (status.status === 'failed') {
        ElMessage.error(`AI生成失败: ${status.error}`)
        stopStatusPolling()
        generating.value = false
      } else if (status.status === 'cancelled') {
        ElMessage.warning('AI生成任务已取消')
        stopStatusPolling()
        generating.value = false
      }
    } catch (error: any) {
      console.error('查询任务状态失败:', error)
      ElMessage.error('查询任务状态失败')
      stopStatusPolling()
      generating.value = false
    }
  }, 3000) // 每3秒查询一次
}

// 停止状态轮询
const stopStatusPolling = () => {
  if (statusPolling.value) {
    clearInterval(statusPolling.value)
    statusPolling.value = null
  }
}

// 保存模板
const saveTemplate = async () => {
  if (!saveForm.value.template_name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  
  if (!currentTaskId.value) {
    ElMessage.error('没有可保存的模板')
    return
  }
  
  saving.value = true
  try {
    const savedTemplate = await saveAIGeneratedTemplate(currentTaskId.value, {
      template_name: saveForm.value.template_name.trim(),
      template_description: saveForm.value.template_description.trim()
    })
    
    ElMessage.success('模板保存成功！')
    showSaveDialog.value = false
    
    // 重置表单
    saveForm.value.template_name = ''
    saveForm.value.template_description = ''
    
    // 可以跳转到模板列表页面
    // router.push('/admin/prompt-templates')
    
  } catch (error: any) {
    console.error('保存模板失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存模板失败')
  } finally {
    saving.value = false
  }
}

// 取消生成
const cancelGeneration = async () => {
  if (!currentTaskId.value) return

  try {
    await cancelAIGeneration(currentTaskId.value)
    ElMessage.success('任务已取消')
    stopStatusPolling()
    generating.value = false
  } catch (error: any) {
    console.error('取消任务失败:', error)
    ElMessage.error(error.response?.data?.detail || '取消任务失败')
  }
}



// 清空提示词
const clearPrompt = () => {
  promptInput.value = ''
}

// 内容变化处理
const onContentChange = (content: string) => {
  generatedContent.value = content
  emit('template-generated', content)
}

// 下一步
const handleNext = () => {
  if (!generatedContent.value.trim()) {
    ElMessage.warning('请先生成模板内容')
    return
  }
  emit('next')
}

// 初始化
onMounted(async () => {
  await variablesStore.fetchVariables()
  
  // 初始化变量数据，核心变量默认勾选
  variables.value = variablesStore.variables.map(v => ({
    ...v,
    selected: v.group === 'core' // 核心变量默认勾选
  }))
})

// 组件卸载时清理轮询
onUnmounted(() => {
  stopStatusPolling()
})
</script>

<style scoped>
.step-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%; /* 相对于父容器 */
  min-height: 0;
  box-sizing: border-box;
  padding: 2vh 2vw;
}

.step-header {
  margin-bottom: 2vh;
  flex-shrink: 0;
  text-align: center;
  margin-top: -1vh;
}

.step-header h3 {
  margin: 0 0 0.5vh 0;
  color: #2c3e50;
  font-size: clamp(16px, 2.2vw, 22px);
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.step-header p {
  margin: 0;
  color: #6b7280;
  font-size: clamp(12px, 1.4vw, 14px);
  line-height: 1.5;
}

.ai-generation-content {
  flex: 1;
  display: flex;
  min-height: 0;
  height: 100%; /* 相对于父容器 */
  overflow: hidden;
  position: relative; /* 为绝对定位的子元素提供定位上下文 */
}

.variables-container {
  position: absolute; /* 绝对定位，按固定位置分割父容器 */
  left: 0;
  top: 0;
  width: 50px; /* 折叠状态宽度，固定位置分割 */
  height: 100%; /* 高度由父容器提供 */
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #d1d5db;
  display: flex;
  flex-direction: column;
  transition: width 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 10; /* 变量区域z轴在内容区域上面 */
}

.variables-panel {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #d1d5db;
  border-radius: 16px;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  width: 100%; /* 占满容器宽度 */
  height: 100%; /* 相对于variables-container的高度 */
  position: relative; /* 相对定位，在容器内部 */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* 书卷卷轴装饰 */
.scroll-rod {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 8px;
  background: linear-gradient(180deg, #8b5cf6 0%, #6366f1 50%, #8b5cf6 100%);
  border-radius: 4px;
  z-index: 2;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.left-rod {
  left: 0;
  transform: translateX(-100%);
}

.right-rod {
  right: 0;
  transform: translateX(100%);
}

.variables-panel:not(.collapsed) {
  width: 100%;
  min-width: 250px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

/* 展开状态时，变量容器遮盖更多内容区域 */
.variables-container:has(.variables-panel:not(.collapsed)) {
  width: 500px; /* 展开状态宽度 */
  z-index: 10; /* 确保在最上层 */
}

.variables-panel:not(.collapsed) .left-rod {
  transform: translateX(0);
}

.variables-panel:not(.collapsed) .right-rod {
  transform: translateX(0);
}

/* 书卷纸张效果 */
.scroll-paper {
  background: #ffffff;
  border-radius: 12px;
  padding: 1.5vh 1.5vw;
  margin: 8px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.variables-panel.collapsed {
  padding: 0;
  overflow: hidden;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #d1d5db;
  height: 100%; /* 保持与展开状态相同的高度计算 */
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}

/* 折叠状态下，内容区域只显示50px宽度 */
.variables-panel.collapsed .scroll-paper {
  width: 50px;
  overflow: hidden;
}

.variables-panel.collapsed .scroll-paper {
  opacity: 0;
  transform: scale(0.8) translateX(-10px);
  margin: 0;
  padding: 0;
}

.variables-panel.collapsed .header-content,
.variables-panel.collapsed .variables-list,
.variables-panel.collapsed .variables-actions {
  opacity: 0;
  transform: translateX(-20px) scale(0.95);
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  height: 0;
  overflow: hidden;
}

.variables-panel:not(.collapsed) .header-content,
.variables-panel:not(.collapsed) .variables-list,
.variables-panel:not(.collapsed) .variables-actions {
  opacity: 1;
  transform: translateX(0) scale(1);
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: auto;
  height: auto;
  overflow: visible;
}

.expand-hint-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  background: transparent;
  border-radius: 12px;
  z-index: 3;
  transition: opacity 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.scroll-unroll-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.scroll-shadow {
  width: 20px;
  height: 4px;
  background: linear-gradient(90deg, transparent 0%, rgba(139, 92, 246, 0.3) 50%, transparent 100%);
  border-radius: 2px;
  animation: shadow-pulse 2s infinite;
}

/* 折叠状态下的展开提示 */
.variables-panel.collapsed .expand-hint-overlay {
  opacity: 1;
  pointer-events: auto;
}

/* 展开状态下的展开提示 */
.variables-panel:not(.collapsed) .expand-hint-overlay {
  opacity: 0;
  pointer-events: none;
}

.variables-panel:not(.collapsed) .expand-hint {
  opacity: 0;
  transform: translateX(10px);
  pointer-events: none;
}

.expand-icon {
  font-size: 20px;
  color: #6366f1;
  animation: pulse 2s infinite;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.variables-panel:hover .expand-icon {
  transform: scale(1.1);
}



@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

@keyframes shadow-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scaleX(0.8);
  }
  50% {
    opacity: 0.6;
    transform: scaleX(1.2);
  }
}

/* 书卷展开时的纸张卷动效果 */
.variables-panel:not(.collapsed) .scroll-paper {
  animation: paper-unroll 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes paper-unroll {
  0% {
    opacity: 0;
    transform: scale(0.8) translateX(-10px) rotateY(-15deg);
  }
  50% {
    opacity: 0.7;
    transform: scale(0.9) translateX(-5px) rotateY(-8deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateX(0) rotateY(0deg);
  }
}

.panel-header {
  margin-bottom: 1.5vh;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-content {
  flex: 1;
}

.panel-header h4 {
  margin: 0 0 0.5vh 0;
  color: #374151;
  font-size: clamp(14px, 1.6vw, 16px);
  font-weight: 600;
}

.panel-header p {
  margin: 0 0 1vh 0;
  color: #6b7280;
  font-size: clamp(11px, 1.2vw, 13px);
  line-height: 1.4;
}

.variables-actions {
  display: flex;
  gap: 0.5vw;
  margin-top: 0.5vh;
}

.variables-actions .el-button {
  font-size: clamp(10px, 1.1vw, 12px);
  padding: 0.3vh 0.8vw;
  height: auto;
}

.variables-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.8vh;
  min-height: 0; /* 允许收缩 */
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  padding: 0.8vh 0.5vw;
  border-radius: 6px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.variable-item:hover {
  background: #f9fafb;
}

.variable-item code {
  background: #f3f4f6;
  color: #6366f1;
  padding: 0.2vh 0.5vw;
  border-radius: 4px;
  font-size: clamp(11px, 1.2vw, 13px);
  font-weight: 600;
  flex-shrink: 0;
}

.variable-desc {
  color: #6b7280;
  font-size: clamp(10px, 1.1vw, 12px);
  line-height: 1.4;
  flex: 1;
}

/* 复选框样式优化 */
.variables-list :deep(.el-checkbox) {
  width: 100%;
  margin-right: 0;
}

.variables-list :deep(.el-checkbox__label) {
  width: 100%;
  padding-left: 0.5vw;
}

.variables-list :deep(.el-checkbox__input) {
  margin-right: 0.5vw;
}

.ai-generation-panel {
  position: absolute; /* 绝对定位，从固定位置开始 */
  left: 50px; /* 从变量区域折叠宽度开始，给变量区域留折叠空间 */
  top: 0;
  right: 0; /* 占据父容器右侧所有空间 */
  height: 100%; /* 高度由父容器提供 */
  display: flex;
  flex-direction: column;
  gap: 2vh;
  min-height: 0;
  overflow: hidden;
  z-index: 1; /* 内容区域z轴在变量区域下面 */
}

.prompt-input-section,
.generation-result-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5vh 1.5vw;
  display: flex;
  flex-direction: column;
}

.prompt-input-section {
  flex: 0 0 auto;
}

.generation-result-section {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-header {
  margin-bottom: 1.5vh;
  flex-shrink: 0;
}

.section-header h4 {
  margin: 0 0 0.5vh 0;
  color: #374151;
  font-size: clamp(14px, 1.6vw, 16px);
  font-weight: 600;
}

.section-header p {
  margin: 0;
  color: #6b7280;
  font-size: clamp(11px, 1.2vw, 13px);
  line-height: 1.4;
}

.prompt-input-container {
  display: flex;
  flex-direction: column;
  gap: 1vh;
}

.prompt-textarea :deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-size: clamp(12px, 1.3vw, 14px);
  line-height: 1.6;
  resize: vertical;
  min-height: 120px;
}

.prompt-actions {
  display: flex;
  gap: 1vw;
  justify-content: flex-end;
}

.generate-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.result-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.empty-state,
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-size: clamp(12px, 1.3vw, 14px);
  gap: 1vh;
}

.empty-state .el-icon,
.loading-state .el-icon {
  font-size: clamp(24px, 3vw, 32px);
  color: #d1d5db;
}

.loading-state .el-icon.is-loading {
  color: #6366f1;
  animation: rotate 1s linear infinite;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.progress-bar {
  width: 200px;
  margin: 8px 0;
}

.progress-text {
  font-size: 14px;
  color: #6366f1;
  font-weight: 500;
}

.cancel-btn {
  margin-left: 8px;
}

.generated-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1vw;
  margin-top: 2vh;
  padding-top: 2vh;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.prev-btn {
  background: #f9fafb;
  border: 1px solid #d1d5db;
  color: #6b7280;
  font-weight: 600;
  border-radius: 12px;
  padding: 0.8vh 2vw;
  font-size: clamp(14px, 1.5vw, 16px);
  transition: all 0.3s ease;
  height: 4vh;
  min-height: 40px;
  max-height: 48px;
  box-sizing: border-box;
}

.prev-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  color: #374151;
  transform: translateY(-1px);
}

.next-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: 12px;
  padding: 0.8vh 2.5vw;
  font-size: clamp(14px, 1.5vw, 16px);
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
  height: 4vh;
  min-height: 40px;
  max-height: 48px;
  box-sizing: border-box;
}

.next-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

.next-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .ai-generation-content {
    grid-template-columns: 1fr 2.5fr;
    gap: 1.5vw;
  }
}

@media (max-width: 768px) {
  .step-panel {
    padding: 1vh 1vw;
  }
  
  .ai-generation-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
    gap: 1vh;
  }
  
  .variables-container {
    max-height: 200px;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 1vh;
  }
  
  .step-actions .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .prompt-actions {
    flex-direction: column;
    gap: 1vh;
  }
  
  .prompt-actions .el-button {
    width: 100%;
  }
}
</style>
