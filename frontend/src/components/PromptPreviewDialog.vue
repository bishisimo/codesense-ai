<template>
  <el-dialog
    v-model="dialogVisible"
    :title="template?.name || '模板预览'"
    width="80%"
    :before-close="handleClose"
    class="preview-dialog"
    :lock-scroll="true"
  >
    <div v-if="template" class="preview-container">
      <div class="preview-header" v-if="template.description">
        <p class="template-description">
          {{ template.description }}
        </p>
      </div>
      
      <div class="preview-content">
        <div class="variables-panel">
          <div class="variables-header">
            <h4>变量值</h4>
          </div>
          <div class="variables-groups">
              <!-- 核心变量组 -->
              <div class="variable-group">
                <div class="group-header">
                  <el-icon><Star /></el-icon>
                  <span>核心变量</span>
                </div>
                <div class="group-variables">
                  <div v-for="variable in coreVariables" :key="variable.name" class="variable-item">
                    <div class="variable-label">
                      <code>{{ variable.name }}</code>
                      <el-tag size="small" type="success">核心</el-tag>
                      <div v-if="variablesUsed.includes(variable.name)" class="used-indicator"></div>
                    </div>
                    <el-input
                      v-model="renderData[variable.name]"
                      :placeholder="variable.description"
                      size="small"
                      @input="updatePreview"
                    />
                  </div>
                </div>
              </div>

              <!-- 扩展变量组 -->
              <div class="variable-group">
                <div class="group-header">
                  <el-icon><Setting /></el-icon>
                  <span>扩展变量</span>
                </div>
                <div class="group-variables">
                  <div v-for="variable in extendedVariables" :key="variable.name" class="variable-item">
                    <div class="variable-label">
                      <code>{{ variable.name }}</code>
                      <el-tag size="small" type="warning">扩展</el-tag>
                      <div v-if="variablesUsed.includes(variable.name)" class="used-indicator"></div>
                    </div>
                    <el-input
                      v-model="renderData[variable.name]"
                      :placeholder="variable.description"
                      size="small"
                      @input="updatePreview"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        
        <div class="preview-result">
          <h4>渲染结果</h4>
          <div class="markdown-preview" v-html="renderedMarkdown"></div>
        </div>
        

      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Warning, Star, Setting } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { 
  renderTemplate, 
  getTemplateVariables,
  type PromptTemplate,
  type TemplateVariableInfo
} from '@/api/prompt'
import JinjaEditor from './JinjaEditor.vue'

// Props
interface Props {
  modelValue: boolean
  template?: PromptTemplate | null
}

const props = withDefaults(defineProps<Props>(), {
  template: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 响应式数据
const loading = ref(false)
const error = ref('')
const availableVariables = ref<TemplateVariableInfo[]>([])
const renderData = reactive<Record<string, string>>({})
const renderedContent = ref('')
const variablesUsed = ref<string[]>([])

// Markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 变量分组
const coreVariables = computed(() => {
  return availableVariables.value.filter(v => v.group === 'core')
})

const extendedVariables = computed(() => {
  return availableVariables.value.filter(v => v.group === 'extended')
})

// 渲染Markdown内容
const renderedMarkdown = computed(() => {
  if (!renderedContent.value) {
    return '<p>暂无渲染内容</p>'
  }
  
  try {
    return md.render(renderedContent.value)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return '<p>Markdown渲染失败</p>'
  }
})

// 获取可用变量
const fetchVariables = async () => {
  try {
    const response = await getTemplateVariables()
    availableVariables.value = response.variables
    
    // 初始化渲染数据
    response.variables.forEach((variable: TemplateVariableInfo) => {
      renderData[variable.name] = variable.example || ''
    })
  } catch (error) {
    console.error('获取变量列表失败:', error)
    ElMessage.error('获取变量列表失败')
  }
}

// 更新预览
const updatePreview = async () => {
  if (!props.template?.id) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await renderTemplate(props.template.id, {
      render_data: renderData
    })
    renderedContent.value = response.rendered_content
    variablesUsed.value = response.variables_used
  } catch (err: any) {
    console.error('预览失败:', err)
    error.value = err.message || '预览失败'
  } finally {
    loading.value = false
  }
}

// 监听模板变化
watch(() => props.template, (template) => {
  if (template) {
    // 初始化渲染数据
    availableVariables.value.forEach(variable => {
      renderData[variable.name] = variable.example || ''
    })
    updatePreview()
  }
}, { immediate: true })



// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false
}

// 初始化
fetchVariables()
</script>

<style scoped>
:deep(.preview-dialog) {
  margin: 0 !important;
}

:deep(.preview-dialog .el-overlay) {
  overflow: hidden !important;
}

:deep(.preview-dialog .el-dialog) {
  height: 80vh;
  max-height: 80vh;
  margin: 0 auto;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

:deep(.preview-dialog .el-dialog__header) {
  flex-shrink: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #dcdfe6;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

:deep(.preview-dialog .el-dialog__body) {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  min-height: 0;
}

:deep(.preview-dialog .el-dialog__footer) {
  flex-shrink: 0;
  padding: 16px 20px;
  border-top: 1px solid #dcdfe6;
  background: #f8f9fa;
  border-radius: 0 0 8px 8px;
}

.preview-container {
  height: 100%;
  overflow: hidden;
}

.preview-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #dcdfe6;
}

.preview-header h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.template-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.preview-content {
  display: grid;
  grid-template-columns: 30% 1fr;
  gap: 20px;
  height: calc(80vh - 200px);
  overflow: hidden;
}

.variables-panel {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.preview-result {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  min-height: 0;
}

.variables-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.variables-header h4 {
  margin: 0;
  color: #303133;
}

.variables-groups {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-right: 8px;
}

.variable-group {
  margin-bottom: 20px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.group-variables {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.variable-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.variable-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.variable-label code {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 3px;
  color: #409eff;
  font-size: 11px;
}

.used-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #67c23a;
  flex-shrink: 0;
}

.preview-result h4 {
  margin: 0 0 16px 0;
  color: #303133;
  flex-shrink: 0;
}

.editor-container {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-container :deep(.jinja-editor-container) {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-container :deep(.editor-wrapper) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-container :deep(.jinja-textarea) {
  flex: 1;
  min-height: 0;
  resize: none;
  height: auto !important;
}

.rendered-content {
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
}

.rendered-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.error {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f56c6c;
}

.markdown-preview {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 20px;
  height: 100%;
  min-height: 400px;
  overflow-y: auto;
  line-height: 1.6;
  color: #303133;
}

.markdown-preview :deep(h1) {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
}

.markdown-preview :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 24px 0 12px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #e4e7ed;
}

.markdown-preview :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 8px 0;
}

.markdown-preview :deep(h4) {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 16px 0 6px 0;
}

.markdown-preview :deep(p) {
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.markdown-preview :deep(ul), .markdown-preview :deep(ol) {
  margin: 0 0 12px 0;
  padding-left: 20px;
}

.markdown-preview :deep(li) {
  margin: 4px 0;
  line-height: 1.5;
}

.markdown-preview :deep(strong) {
  font-weight: 600;
  color: #409eff;
}

.markdown-preview :deep(code) {
  background: #f5f7fa;
  color: #e6a23c;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.markdown-preview :deep(pre) {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin: 12px 0;
  overflow-x: auto;
}

.markdown-preview :deep(pre code) {
  background: none;
  color: #303133;
  padding: 0;
  border-radius: 0;
}

.markdown-preview :deep(blockquote) {
  border-left: 4px solid #409eff;
  background: #f0f9ff;
  margin: 12px 0;
  padding: 12px 16px;
  color: #606266;
}

.markdown-preview :deep(hr) {
  border: none;
  border-top: 2px solid #e4e7ed;
  margin: 24px 0;
}



.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  :deep(.preview-dialog .el-dialog) {
    width: 85% !important;
    height: 85vh;
    max-height: 85vh;
  }
  
  .preview-content {
    grid-template-columns: 35% 1fr;
    height: calc(85vh - 200px);
  }
}

@media (max-width: 768px) {
  :deep(.preview-dialog .el-dialog) {
    width: 95% !important;
    height: 90vh;
    max-height: 90vh;
  }
  
  .preview-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
    height: calc(90vh - 200px);
  }
  
  .variables-panel {
    max-height: 80vh;
  }
}

@media (max-width: 480px) {
  :deep(.preview-dialog .el-dialog) {
    width: 98% !important;
    height: 95vh;
    max-height: 95vh;
  }
  
  .preview-content {
    height: calc(95vh - 200px);
  }
}
</style>
