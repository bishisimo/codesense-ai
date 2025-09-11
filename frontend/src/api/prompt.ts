import request from './index'

export interface PromptTemplate {
  id: number
  name: string
  description?: string
  template_content: string
  variables_schema: string[] | Record<string, any>  // 支持列表或字典格式
  // output_format 字段已移除，由后端统一管理
  is_default: boolean
  is_active: boolean
  generation_status: 'pending' | 'success' | 'failed'
  validation_errors?: string
  ai_generated: boolean
  created_at: string
  updated_at: string
  created_by: string
}

export interface PromptTemplateListResponse {
  items: PromptTemplate[]
  total: number
  page: number
  size: number
  pages: number
}

export interface PromptTemplateCreate {
  name: string
  description?: string
  template_content: string
  variables_schema: string[] | Record<string, any>  // 支持列表或字典格式
  // output_format 字段已移除，由后端统一管理
  is_active: boolean
}

export interface PromptTemplateUpdate {
  name?: string
  description?: string
  template_content?: string
  variables_schema?: string[] | Record<string, any>  // 支持列表或字典格式
  // output_format 字段已移除，由后端统一管理
  is_active?: boolean
}

export interface TemplateRenderRequest {
  render_data: Record<string, any>
}

export interface TemplateRenderResponse {
  rendered_content: string
  variables_used: string[]
  errors: string[]
}

export interface TemplateTestRequest {
  template_content: string
  variables_schema: string[] | Record<string, any>  // 支持列表或字典格式
  // output_format 字段已移除，由后端统一管理
  test_data: Record<string, any>
}

export interface TemplateTestResponse {
  rendered_content: string
  rendered_prompt: string
  validation_result: {
    valid: boolean
    errors: string[]
    warnings: string[]
  }
  test_success: boolean
}

export interface TemplateVariableInfo {
  name: string
  description: string
  type: string
  required: boolean
  example?: string
  group: string
}

export interface TemplateVariablesResponse {
  variables: TemplateVariableInfo[]
}

export interface AITemplateGenerationRequest {
  prompt: string
  selected_variables: string[]
  template_name?: string
  description?: string
}

export interface AITemplateGenerationResponse {
  success: boolean
  template_content: string
  variables_used: string[]
  tokens_used: number
  generation_time: number
  validation_errors: string[]
  generation_status: 'pending' | 'success' | 'failed'
  message: string
}

// 获取模板列表
export function getPromptTemplates(params?: {
  page?: number
  size?: number
  name?: string
  is_active?: boolean
  sort_by?: string
  sort_order?: string
}) {
  return request<PromptTemplateListResponse>({
    url: '/prompt-templates',
    method: 'GET',
    params
  })
}

// 创建模板
export function createPromptTemplate(data: PromptTemplateCreate) {
  return request<PromptTemplate>({
    url: '/prompt-templates',
    method: 'POST',
    data
  })
}

// 获取模板详情
export function getPromptTemplate(id: number) {
  return request<PromptTemplate>({
    url: `/prompt-templates/${id}`,
    method: 'GET'
  })
}

// 更新模板
export function updatePromptTemplate(id: number, data: PromptTemplateUpdate) {
  return request<PromptTemplate>({
    url: `/prompt-templates/${id}`,
    method: 'PUT',
    data
  })
}

// 删除模板
export function deletePromptTemplate(id: number) {
  return request<{ message: string }>({
    url: `/prompt-templates/${id}`,
    method: 'DELETE'
  })
}

// 设置默认模板
export function setDefaultTemplate(id: number) {
  return request<{ message: string }>({
    url: `/prompt-templates/${id}/set-default`,
    method: 'POST'
  })
}

// 渲染模板
export function renderTemplate(id: number, data: TemplateRenderRequest) {
  return request<TemplateRenderResponse>({
    url: `/prompt-templates/${id}/render`,
    method: 'POST',
    data
  })
}


// 获取模板变量
export function getTemplateVariables() {
  return request<TemplateVariablesResponse>({
    url: '/prompt-templates/variables',
    method: 'GET'
  })
}

// AI生成模板
export function generateAITemplate(data: AITemplateGenerationRequest) {
  return request<{ task_id: string; message: string }>({
    url: '/prompt-templates/ai-generate',
    method: 'POST',
    data
  })
}

export function getAIGenerationStatus(taskId: string) {
  return request<{
    task_id: string
    status: string
    result: any
    error: string | null
    created_at: string
    started_at: string | null
    completed_at: string | null
    progress: number
    message: string
  }>({
    url: `/prompt-templates/ai-generate/${taskId}/status`,
    method: 'GET'
  })
}

export function getAIGenerationResult(taskId: string) {
  return request<AITemplateGenerationResponse>({
    url: `/prompt-templates/ai-generate/${taskId}/result`,
    method: 'GET'
  })
}

// 保存AI生成的模板
export function saveAIGeneratedTemplate(taskId: string, data: {
  template_name: string
  template_description?: string
}) {
  return request<PromptTemplate>({
    url: `/prompt-templates/ai-generate/${taskId}/save`,
    method: 'POST',
    data
  })
}

export function cancelAIGeneration(taskId: string) {
  return request<{ message: string }>({
    url: `/prompt-templates/ai-generate/${taskId}/cancel`,
    method: 'POST'
  })
}
