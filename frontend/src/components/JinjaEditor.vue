<template>
  <div class="jinja-editor-container">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <span class="editor-label">Jinja2模板编辑器</span>
        <el-tag size="small" type="info">支持语法高亮</el-tag>
      </div>
      <div class="toolbar-right">
        <el-button size="small" @click="formatCode" :icon="Operation">
          格式化
        </el-button>
        <el-button size="small" @click="clearCode" :icon="Delete">
          清空
        </el-button>
      </div>
    </div>
    <div class="editor-wrapper">
      <textarea
        ref="textareaRef"
        v-model="localValue"
        :placeholder="placeholder"
        :readonly="readOnly"
        class="jinja-textarea"
        :style="{ height }"
        @input="handleInput"
        @keydown="handleKeydown"
      ></textarea>
      <div class="editor-info">
        <div class="info-item">
          <el-icon><Document /></el-icon>
          <span>字符数: {{ localValue.length }}</span>
        </div>
        <div class="info-item">
          <el-icon><InfoFilled /></el-icon>
          <span>变量数量: {{ variableCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation, Delete, Document, InfoFilled } from '@element-plus/icons-vue'

// Props
interface Props {
  modelValue: string
  placeholder?: string
  height?: string
  readOnly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请输入Jinja2模板内容，使用 {{ 变量名 }} 语法插入变量',
  height: '400px',
  readOnly: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string]
}>()

// 响应式数据
const textareaRef = ref<HTMLTextAreaElement>()
const localValue = ref(props.modelValue)

// 计算属性
const variableCount = computed(() => {
  const matches = localValue.value.match(/\{\{\s*(\w+)\s*\}\}/g)
  return matches ? new Set(matches.map(m => m.replace(/\{\{\s*|\s*\}\}/g, ''))).size : 0
})

// 处理输入
const handleInput = () => {
  emit('update:modelValue', localValue.value)
  emit('change', localValue.value)
}

// 处理键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Tab') {
    e.preventDefault()
    const textarea = e.target as HTMLTextAreaElement
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    
    // 插入制表符
    const newValue = localValue.value.substring(0, start) + '  ' + localValue.value.substring(end)
    localValue.value = newValue
    
    // 设置光标位置
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 2
    })
  }
}

// 格式化代码
const formatCode = () => {
  try {
    let formatted = localValue.value
      // 移除多余的空行
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      // 统一缩进
      .replace(/^\s+/gm, '')
      // 在Jinja2标签前后添加适当的空格
      .replace(/([^}])\{\{/g, '$1 {{')
      .replace(/\}\}([^{])/g, '}} $1')
      .replace(/([^}])\{%/g, '$1 {%')
      .replace(/%\}([^{])/g, '%} $1')
    
    localValue.value = formatted
    ElMessage.success('代码格式化完成')
  } catch (error) {
    ElMessage.error('格式化失败')
  }
}

// 清空代码
const clearCode = () => {
  localValue.value = ''
  ElMessage.success('代码已清空')
}

// 获取编辑器值
const getValue = () => {
  return localValue.value
}

// 设置编辑器值
const setValue = (value: string) => {
  localValue.value = value
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (localValue.value !== newValue) {
    localValue.value = newValue
  }
})

// 监听高度变化
watch(() => props.height, (newHeight) => {
  if (textareaRef.value) {
    textareaRef.value.style.height = newHeight
  }
})

// 监听只读状态变化
watch(() => props.readOnly, (readOnly) => {
  if (textareaRef.value) {
    textareaRef.value.readOnly = readOnly
  }
})

// 暴露方法给父组件
defineExpose({
  getValue,
  setValue,
  formatCode,
  clearCode
})

// 生命周期
onMounted(() => {
  if (textareaRef.value) {
    textareaRef.value.style.height = props.height
    textareaRef.value.readOnly = props.readOnly
  }
})
</script>

<style scoped>
.jinja-editor-container {
  border: 2px solid #e1e8ed;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  background: white;
}

.jinja-editor-container:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-color: #667eea;
  transform: translateY(-2px);
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 2px solid #e1e8ed;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.editor-label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 15px;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.toolbar-right .el-button {
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 8px 16px;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.toolbar-right .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.editor-wrapper {
  position: relative;
}

.jinja-textarea {
  width: 100%;
  min-height: 200px;
  border: none;
  outline: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.6;
  padding: 20px;
  background: #fafbfc;
  color: #2c3e50;
  resize: vertical;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.jinja-textarea::placeholder {
  color: #6c757d;
  font-style: italic;
}

.jinja-textarea:focus {
  background: #ffffff;
  box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.04);
}

.editor-info {
  display: flex;
  justify-content: space-between;
  padding: 12px 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-top: 2px solid #e1e8ed;
  font-size: 13px;
  color: #2c3e50;
  font-weight: 500;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .el-icon {
  color: #667eea;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .editor-toolbar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }
  
  .editor-info {
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }
  
  .jinja-textarea {
    padding: 16px;
    font-size: 13px;
  }
}
</style>
