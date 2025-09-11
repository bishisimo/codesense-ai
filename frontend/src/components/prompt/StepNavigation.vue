<template>
  <div class="steps-sidebar">
    <div class="steps-nav">
      <div 
        v-for="(step, index) in steps" 
        :key="index"
        class="step-item"
        :class="{ 
          'active': currentStep === index,
          'completed': step.completed,
          'disabled': !step.available
        }"
        @click="goToStep(index)"
      >
        <div class="step-number">{{ index + 1 }}</div>
        <div class="step-content">
          <div class="step-title">{{ step.title }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Step {
  title: string
  description: string
  completed: boolean
  available: boolean
}

interface Props {
  steps: Step[]
  currentStep: number
}

interface Emits {
  (e: 'step-change', index: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const goToStep = (index: number) => {
  if (props.steps[index].available) {
    emit('step-change', index)
  }
}
</script>

<style scoped>
.steps-sidebar {
  width: 7vw; /* 减少宽度 */
  min-width: 100px; /* 减少最小宽度 */
  max-width: 140px; /* 减少最大宽度 */
  background: linear-gradient(135deg, #fafbfc 0%, #f8fafc 100%);
  border-right: 1px solid #e2e8f0;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
  flex-shrink: 0;
  box-sizing: border-box;
}

.steps-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0.15) 100%);
  pointer-events: none;
}

.steps-nav {
  display: flex;
  flex-direction: column;
  gap: 4vh; /* 减少间距 */
  width: 100%;
  padding: 1.5vh 0.5vw; /* 减少内边距 */
  position: relative;
  z-index: 1;
  height: 100%;
  justify-content: center;
  box-sizing: border-box;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 0.4vw; /* 减少间距 */
  padding: 0.8vh 0.6vw; /* 减少内边距 */
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
  border: 1px solid #e5e7eb;
  border-radius: 6px; /* 减少圆角 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  min-height: 2.5vh; /* 减少最小高度 */
  max-height: 3.5vh; /* 减少最大高度 */
  box-sizing: border-box;
  margin-left: -0.8vw; /* 更靠左 */
}

.step-item:hover {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-color: #d1d5db;
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.06);
  margin-left: -0.6vw; /* 更靠左 */
}

.step-item.active {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  border-color: #4338ca !important;
  color: white !important;
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25) !important;
  transform: translateX(6px) translateY(-2px) !important; /* 减少移动距离 */
  z-index: 10;
  margin-left: -0.2vw; /* 更靠左 */
}

.step-item.completed {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: #047857;
  color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transform: none;
  margin-left: -0.8vw;
}

.step-item.completed:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  border-color: #065f46;
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(16, 185, 129, 0.15);
  margin-left: -0.6vw;
}

.step-item.completed .step-number {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #10b981;
  box-shadow: none;
  transform: none;
}

.step-item.completed .step-title {
  color: #374151;
  font-weight: 500;
  text-shadow: none;
}

.step-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  transform: none;
  margin-left: -0.8vw; /* 确保未选中状态也靠左 */
}

.step-item.disabled:hover {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  transform: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  margin-left: -0.8vw; /* 确保悬停状态也靠左 */
}

.step-number {
  width: 20px; /* 减少尺寸 */
  height: 20px; /* 减少尺寸 */
  border-radius: 50%;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: clamp(9px, 1.1vw, 11px); /* 减少字体 */
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.step-item.active .step-number {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
  color: #6366f1 !important;
  box-shadow: 0 3px 8px rgba(255, 255, 255, 0.25) !important;
  transform: scale(1.1);
}

.step-item.completed .step-number {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: #10b981;
  box-shadow: 0 3px 6px rgba(255, 255, 255, 0.25);
}

.step-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: clamp(10px, 1.2vw, 12px); /* 减少字体 */
  font-weight: 500;
  color: #374151;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-item.active .step-title {
  color: white !important;
  font-weight: 600 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.step-item.completed .step-title {
  color: white;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .steps-sidebar {
    width: 120px; /* 减少宽度 */
  }
  
  .steps-nav {
    gap: 12px; /* 减少间距 */
    padding: 0 12px; /* 减少内边距 */
  }
  
  .step-item {
    padding: 8px 12px; /* 减少内边距 */
    gap: 6px; /* 减少间距 */
    height: 32px; /* 减少高度 */
  }
  
  .step-number {
    width: 20px; /* 减少尺寸 */
    height: 20px; /* 减少尺寸 */
    font-size: 10px; /* 减少字体 */
  }
  
  .step-title {
    font-size: 11px; /* 减少字体 */
  }
}

@media (max-width: 768px) {
  .steps-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    padding: 12px 0;
    min-height: auto;
  }
  
  .steps-nav {
    flex-direction: row;
    justify-content: space-around;
    gap: 12px;
    padding: 0 16px;
  }
  
  .step-item {
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    text-align: center;
    flex: 1;
    height: auto;
    border-radius: 8px;
    transform: none;
  }
  
  .step-item:hover,
  .step-item.active {
    transform: translateY(-2px);
  }
  
  .step-number {
    width: 20px;
    height: 20px;
    font-size: 10px;
  }
  
  .step-content {
    align-items: center;
  }
  
  .step-title {
    font-size: 11px;
  }
}
</style>
