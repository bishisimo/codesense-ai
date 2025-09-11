<template>
  <div class="step-panel">
    <div class="step-form">
      <div class="editor-section">
        <div class="editor-header">
          <div class="editor-title">
            <el-icon><Edit /></el-icon>
            <span>Jinja2模板编辑器</span>
          </div>
          <div class="editor-actions">
            <el-button size="small" @click="$emit('insert-variable')" :icon="Plus" class="action-btn">
              插入变量
            </el-button>
          </div>
        </div>
        <div class="editor-content">
          <textarea
            ref="templateTextarea"
            v-model="form.template_content"
            class="template-textarea"
            placeholder="请输入Jinja2模板内容，使用 {{ 变量名 }} 语法插入变量"
            @input="onTemplateChange"
          ></textarea>
          <div class="editor-info">
            <span>字符数: {{ form.template_content.length }}</span>
            <span>变量数量: {{ variableCount }}</span>
          </div>
        </div>
      </div>
    </div>
    

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Plus } from '@element-plus/icons-vue'

interface FormData {
  template_content: string
}

interface Props {
  form: FormData
}

interface Emits {
  (e: 'next'): void
  (e: 'prev'): void
  (e: 'insert-variable'): void
  (e: 'template-change', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const templateTextarea = ref<HTMLTextAreaElement>()

// 计算变量数量
const variableCount = computed(() => {
  const matches = props.form.template_content.match(/\{\{\s*(\w+)\s*\}\}/g)
  return matches ? new Set(matches.map(m => m.replace(/\{\{\s*|\s*\}\}/g, ''))).size : 0
})

const onTemplateChange = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  const value = target.value
  emit('template-change', value)
}

const handleNext = async () => {
  emit('next')
}
</script>

<style scoped>
.step-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  padding: 2vh 2vw;
}

.step-header {
  margin-bottom: 1.5vh;
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

.step-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e1e8ed;
  border-radius: 12px;
  overflow: hidden;
  background: #fafbfc;
  min-height: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6vh 1vw;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.editor-title {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  color: #374151;
  font-weight: 600;
  font-size: clamp(12px, 1.4vw, 14px);
}

.editor-actions {
  display: flex;
  gap: 0.5vw;
}

.action-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #6366f1;
  font-weight: 500;
  border-radius: 8px;
  padding: 0.6vh 1vw;
  font-size: clamp(12px, 1.3vw, 14px);
  transition: all 0.3s ease;
  height: 3vh;
  min-height: 32px;
  max-height: 40px;
  box-sizing: border-box;
}

.action-btn:hover {
  background: #667eea;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.template-textarea {
  flex: 1;
  border: none;
  outline: none;
  padding: 2vh 2vw;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: clamp(14px, 1.5vw, 16px);
  line-height: 1.6;
  background: white;
  resize: none;
  min-height: 0;
  color: #374151;
}

.editor-info {
  display: flex;
  justify-content: space-between;
  padding: 0.8vh 1.5vw;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  font-size: clamp(12px, 1.3vw, 14px);
  color: #6b7280;
  flex-shrink: 0;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1vw;
  margin-top: 1vh;
  padding-top: 1vh;
  border-top: 1px solid #e9ecef;
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
  background: #e9ecef;
  border-color: #adb5bd;
  color: #495057;
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

.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .template-textarea {
    height: 450px;
  }
}

@media (max-width: 768px) {
  .step-header h3 {
    font-size: 24px;
  }
  
  .step-header p {
    font-size: 14px;
  }
  
  .template-textarea {
    height: 400px;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .step-actions .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .template-textarea {
    height: 350px;
  }
}
</style>
