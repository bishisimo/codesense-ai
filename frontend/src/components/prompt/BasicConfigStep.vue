<template>
  <div class="step-panel">
    <div class="step-header">
      <h3>基础配置</h3>
      <p>设置模板的基本信息和状态</p>
    </div>
    
    <div class="step-form">
      <div class="form-section">
        <div class="form-item">
          <label class="form-label">模板名称</label>
          <el-input 
            v-model="form.name" 
            placeholder="请输入模板名称"
            size="large"
          />
        </div>
        
        <div class="form-item">
          <label class="form-label">状态</label>
          <div class="switch-container">
            <el-switch 
              v-model="form.is_active" 
              size="large"
              active-text="启用"
              inactive-text="禁用"
            />
            <span class="switch-hint">控制模板是否可用</span>
          </div>
        </div>
      </div>
      
      <div class="form-section">
        <div class="form-item">
          <label class="form-label">描述</label>
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="6"
            placeholder="请输入模板描述，详细说明模板的用途和特点"
            size="large"
          />
        </div>
      </div>
    </div>
    
    <div class="step-actions">
      <el-button @click="$emit('cancel')" class="cancel-btn">取消</el-button>
      <el-button type="primary" @click="handleNext" class="next-btn">下一步</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

interface FormData {
  name: string
  description: string
  is_active: boolean
}

interface Props {
  form: FormData
}

interface Emits {
  (e: 'next'): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 监听表单数据变化，用于调试
watch(() => props.form, (newForm) => {
  console.log('BasicConfigStep form changed:', newForm)
}, { deep: true })

const handleNext = async () => {
  console.log('handleNext called, form data:', props.form)
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

.step-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  gap: 3vh;
}

.form-section {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 2vh 2vw;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.form-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 4vh;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: clamp(14px, 1.5vw, 16px);
  margin-bottom: 2vh;
  line-height: 1.5;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.step-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 1px solid #d1d5db;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  height: 5vh;
  min-height: 48px;
  max-height: 56px;
  display: flex;
  align-items: center;
}

.step-form :deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.step-form :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.step-form :deep(.el-input__inner) {
  height: 100%;
  font-size: clamp(13px, 1.4vw, 15px);
  line-height: 1.5;
}

.step-form :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #d1d5db;
  resize: vertical;
  min-height: 10vh;
  max-height: 18vh;
  font-size: clamp(13px, 1.4vw, 15px);
  line-height: 1.6;
  padding: 1.5vh 1.2vw;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.step-form :deep(.el-textarea__inner:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.step-form :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.switch-container {
  display: flex;
  align-items: center;
  gap: 1vw;
}

.switch-hint {
  color: #6b7280;
  font-size: clamp(11px, 1.2vw, 13px);
  font-style: italic;
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

.cancel-btn {
  background: #f9fafb;
  border: 1px solid #d1d5db;
  color: #6b7280;
  font-weight: 600;
  border-radius: 12px;
  padding: 0.8vh 2vw;
  font-size: clamp(13px, 1.4vw, 15px);
  transition: all 0.3s ease;
  height: 4vh;
  min-height: 40px;
  max-height: 48px;
  box-sizing: border-box;
}

.cancel-btn:hover {
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
  font-size: clamp(13px, 1.4vw, 15px);
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
  height: 4vh;
  min-height: 40px;
  max-height: 48px;
  box-sizing: border-box;
}

.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .step-panel {
    padding: 1vh 1vw;
  }
  
  .step-header {
    margin-bottom: 2vh;
  }
  
  .step-header h3 {
    font-size: 20px;
  }
  
  .step-header p {
    font-size: 14px;
  }
  
  .form-section {
    padding: 1.5vh 1.5vw;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 1vh;
  }
  
  .step-actions .el-button {
    width: 100%;
  }
}
</style>
