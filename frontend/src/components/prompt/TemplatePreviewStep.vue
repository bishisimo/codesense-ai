<template>
  <div class="template-preview-step">
    <div class="step-header">
      <h3>模板预览</h3>
      <p class="step-description">预览AI生成的模板内容，确认无误后提交</p>
    </div>

    <div class="preview-content">
      <!-- 模板内容预览 -->
      <div class="preview-section">
        <h4>模板内容预览</h4>
        <div class="markdown-preview" v-html="renderedMarkdown"></div>
      </div>

      <!-- 标准化输出格式说明 -->
      <div class="preview-section">
        <h4>标准化输出格式</h4>
        <div class="output-format-info">
          <p class="info-text">
            本系统使用标准化的审查结果格式，无需手动定义。AI将自动生成符合以下结构的审查结果：
          </p>
          
          <div class="format-structure">
            <div class="format-item">
              <strong>score</strong> - 总体评分 (0-100)
            </div>
            <div class="format-item">
              <strong>level</strong> - 审查级别 (low/medium/high/critical)
            </div>
            <div class="format-item">
              <strong>summary</strong> - 审查总结
            </div>
            <div class="format-item">
              <strong>categories</strong> - 分类评分数组
            </div>
            <div class="format-item">
              <strong>issues</strong> - 发现的问题数组
            </div>
          </div>
          
          <div class="format-note">
            <el-icon><InfoFilled /></el-icon>
            <span>使用标准化格式确保审查结果的一致性和可分析性</span>
          </div>
        </div>
      </div>

      <!-- 变量信息 -->
      <div class="preview-section" v-if="Object.keys(form.variables_schema || {}).length > 0">
        <h4>模板变量</h4>
        <div class="variables-info">
          <div 
            v-for="(schema, varName) in form.variables_schema" 
            :key="varName"
            class="variable-item"
          >
            <span class="variable-name">{{ varName }}</span>
            <span class="variable-desc">{{ schema.description }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="step-actions">
      <el-button @click="$emit('prev')" :icon="ArrowLeft">
        上一步
      </el-button>
      
      <el-button 
        type="primary" 
        @click="$emit('submit')"
        :loading="loading"
        :disabled="!canSubmit"
        :icon="Check"
      >
        创建模板
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ArrowLeft, Check, InfoFilled } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import type { PromptTemplateCreate } from '@/api/prompt'

interface Props {
  form: PromptTemplateCreate
  loading: boolean
  isEdit: boolean
  canSubmit: boolean
}

const props = defineProps<Props>()

defineEmits<{
  prev: []
  submit: []
}>()

// Markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 渲染Markdown内容
const renderedMarkdown = computed(() => {
  if (!props.form.template_content) {
    return '<p>暂无内容</p>'
  }
  
  try {
    return md.render(props.form.template_content)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return '<p>Markdown渲染失败</p>'
  }
})
</script>

<style scoped>
.template-preview-step {
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

.step-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 24px;
}

.preview-section {
  margin-bottom: 24px;
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
}

.preview-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
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

.output-format-info {
  color: #606266;
}

.info-text {
  margin: 0 0 16px 0;
  line-height: 1.6;
}

.format-structure {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.format-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
}

.format-item:last-child {
  border-bottom: none;
}

.format-item strong {
  color: #409eff;
  font-weight: 600;
  margin-right: 12px;
  min-width: 80px;
}

.format-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 6px;
  color: #409eff;
  font-size: 14px;
}

.variables-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.variable-name {
  font-weight: 600;
  color: #409eff;
  margin-right: 16px;
  min-width: 120px;
}

.variable-desc {
  color: #606266;
  flex: 1;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.step-actions .el-button {
  min-width: 100px;
}
</style>
