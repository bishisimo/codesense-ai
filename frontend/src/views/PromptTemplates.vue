<template>
  <div class="prompt-templates">
    <div class="page-header">
      <h2>AI审查Prompt模板管理</h2>
              <div class="header-actions">
          <el-button type="primary" size="default" @click="handleCreate" class="create-btn">
            <el-icon><Plus /></el-icon>
            创建模板
          </el-button>
        </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <el-form :model="searchForm" inline size="default">
        <el-form-item label="模板名称">
          <el-input
            v-model="searchForm.name"
            placeholder="搜索模板名称"
            clearable
            size="default"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="激活状态">
          <el-select v-model="searchForm.is_active" placeholder="选择激活状态" clearable size="default">
            <el-option label="激活" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成状态">
          <el-select v-model="searchForm.generation_status" placeholder="选择生成状态" clearable size="default">
            <el-option label="生成中" value="pending" />
            <el-option label="验证成功" value="success" />
            <el-option label="验证失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="default" @click="handleSearch">搜索</el-button>
          <el-button size="default" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 模板列表 -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="templates"
        style="width: 100%"
        size="default"
        @sort-change="handleSortChange"
        :max-height="tableMaxHeight"
        stripe
        :header-cell-style="{ background: '#f8f9fa', color: '#606266' }"
      >
      <el-table-column prop="name" label="模板名称" sortable="custom" min-width="180" align="center" header-align="center">
        <template #default="{ row }">
          <div class="template-name">
            <span>{{ row.name }}</span>
            <el-tag v-if="row.created_by === 'system'" type="info" size="small">内置</el-tag>
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip align="center" header-align="center" />
      
      <el-table-column prop="is_active" label="激活状态" width="80" align="center" header-align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="generation_status" label="生成状态" width="100" align="center" header-align="center">
        <template #default="{ row }">
          <div v-if="row.ai_generated">
            <el-tag 
              :type="row.generation_status === 'success' ? 'success' : row.generation_status === 'failed' ? 'danger' : 'warning'" 
              size="small"
            >
              {{ row.generation_status === 'success' ? '验证成功' : row.generation_status === 'failed' ? '验证失败' : '生成中' }}
            </el-tag>
            <el-tag v-if="row.ai_generated" type="info" size="small" style="margin-left: 4px">AI</el-tag>
          </div>
          <span v-else>-</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="created_by" label="创建者" width="100" align="center" header-align="center" />
      
      <el-table-column prop="created_at" label="创建时间" sortable="custom" width="160" align="center" header-align="center">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="updated_at" label="更新时间" sortable="custom" width="160" align="center" header-align="center">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" @click="handlePreview(row)">预览</el-button>
            <el-button
              v-if="!row.is_default"
              size="small"
              type="success"
              @click="handleSetDefault(row)"
            >
              设为默认
            </el-button>
            <el-button
              v-if="!row.is_default"
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        :total="pagination.total"
        :page-size="10"
        layout="total, prev, pager, next, jumper"
        size="default"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 预览对话框 -->
    <PromptPreviewDialog
      v-model="showPreviewDialog"
      :template="previewTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { 
  getPromptTemplates, 
  deletePromptTemplate, 
  setDefaultTemplate,
  type PromptTemplate 
} from '@/api/prompt'
import PromptPreviewDialog from '@/components/PromptPreviewDialog.vue'
import { useRouter } from 'vue-router'

// 响应式数据
const loading = ref(false)
const templates = ref<PromptTemplate[]>([])
const showPreviewDialog = ref(false)
const previewTemplate = ref<PromptTemplate | null>(null)

// 表格高度控制
const tableMaxHeight = ref(600)

// 搜索表单
const searchForm = reactive({
  name: '',
  is_active: undefined as boolean | undefined,
  generation_status: undefined as string | undefined
})

// 分页
const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 排序
const sortBy = ref('created_at')
const sortOrder = ref('desc')

// 计算属性
const activeCount = computed(() => templates.value.filter(t => t.is_active).length)

// 获取模板列表
const fetchTemplates = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      name: searchForm.name || undefined,
      is_active: searchForm.is_active,
      generation_status: searchForm.generation_status,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    
    const response = await getPromptTemplates(params)
    // 内置模板置顶，其次默认模板，再其他
    const score = (t: PromptTemplate) => (t.created_by === 'system' ? 2 : 0) + (t.is_default ? 1 : 0)
    templates.value = [...response.items].sort((a, b) => {
      const sa = score(a)
      const sb = score(b)
      if (sa !== sb) return sb - sa
      // 次级排序：保持后端排序（不改变原相对顺序）
      return 0
    })
    pagination.total = response.total
  } catch (error) {
    console.error('获取模板列表失败:', error)
    ElMessage.error('获取模板列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchTemplates()
}

// 重置搜索
const handleReset = () => {
  searchForm.name = ''
  searchForm.is_active = undefined
  searchForm.generation_status = undefined
  pagination.page = 1
  fetchTemplates()
}

// 排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortBy.value = prop
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  fetchTemplates()
}



const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchTemplates()
}

// 编辑模板
const handleEdit = (template: PromptTemplate) => {
  router.push(`/admin/prompt-templates/${template.id}/edit`)
}

// 创建模板（统一入口）
const handleCreate = () => {
  router.push('/admin/prompt-templates/create')
}

// 预览模板
const handlePreview = (template: PromptTemplate) => {
  previewTemplate.value = template
  showPreviewDialog.value = true
}

// 设置默认模板
const handleSetDefault = async (template: PromptTemplate) => {
  try {
    await ElMessageBox.confirm(
      `确定要将模板"${template.name}"设为默认模板吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await setDefaultTemplate(template.id)
    ElMessage.success('设置默认模板成功')
    fetchTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('设置默认模板失败:', error)
      ElMessage.error('设置默认模板失败')
    }
  }
}

// 删除模板
const handleDelete = async (template: PromptTemplate) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deletePromptTemplate(template.id)
    ElMessage.success('删除模板成功')
    fetchTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除模板失败')
    }
  }
}

// 计算表格最大高度
const calculateTableHeight = () => {
  // 计算10条数据的高度：表头(40px) + 10行数据(每行50px)
  const tableContentHeight = 40 + (10 * 50)
  // 设置表格最大高度为10条数据的高度
  tableMaxHeight.value = tableContentHeight
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchTemplates()
  
  // 计算表格高度
  calculateTableHeight()
  
  // 监听窗口大小变化
  window.addEventListener('resize', calculateTableHeight)
})

onUnmounted(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', calculateTableHeight)
})

// 路由
const router = useRouter()
</script>

<style scoped>
.prompt-templates {
  padding: 0;
  background: #f5f7fa;
  min-height: 96vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 16px 16px 16px;
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.ai-create-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.ai-create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
}

.search-bar {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  margin: 0 16px 16px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.search-bar :deep(.el-form-item) {
  margin-right: 16px;
  margin-bottom: 0;
}

.search-bar :deep(.el-form-item__label) {
  min-width: 70px;
  text-align: right;
  margin-right: 8px;
  font-size: 14px;
  color: #606266;
}

.search-bar :deep(.el-input) {
  width: 200px;
}

.search-bar :deep(.el-select) {
  width: 120px;
}

.search-bar :deep(.el-button) {
  margin-left: 8px;
  padding: 8px 16px;
  font-size: 14px;
}

.template-name {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.template-name span {
  font-weight: 500;
  color: #303133;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
}

.action-buttons .el-button {
  padding: 4px 8px;
  font-size: 12px;
  height: 28px;
  line-height: 1;
}

.table-container {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  margin: 0 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin: 16px 16px 16px 16px;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex: 1;
}

/* 表格滚动优化 */
:deep(.el-table__body-wrapper) {
  overflow-y: auto;
  overflow-x: auto;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: #c1c1c1;
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: #a8a8a8;
}

/* 固定列样式优化 */
:deep(.el-table__fixed) {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-table__fixed-right) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

/* 表格行悬停效果 */
:deep(.el-table__body tr:hover > td) {
  background-color: #f8f9fa !important;
}

/* 斑马纹样式优化 */
:deep(.el-table__body tr:nth-child(even)) {
  background-color: #fafbfc;
}

/* 表格行高度优化 */
:deep(.el-table__body tr) {
  height: 50px;
}

:deep(.el-table__header tr) {
  height: 40px;
}

/* 确保表格内容垂直居中 */
:deep(.el-table__body td) {
  padding: 8px 12px;
  vertical-align: middle;
}

:deep(.el-table__header th) {
  padding: 8px 12px;
  vertical-align: middle;
}

:deep(.el-table th) {
  background: #fafafa;
  color: #606266;
  font-weight: 600;
  font-size: 14px;
  padding: 12px 0;
}

:deep(.el-table td) {
  padding: 8px 0;
  font-size: 14px;
}

:deep(.el-table--default) {
  font-size: 14px;
}

/* 标签样式优化 */
:deep(.el-tag) {
  font-size: 12px;
  padding: 2px 6px;
  height: 20px;
  line-height: 16px;
}

/* 分页样式优化 */
:deep(.el-pagination) {
  font-size: 14px;
}

:deep(.el-pagination .el-pager li) {
  padding: 0 8px;
  min-width: 32px;
  height: 32px;
  line-height: 32px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .search-bar :deep(.el-input) {
    width: 180px;
  }
  
  .search-bar :deep(.el-select) {
    width: 100px;
  }
}

@media (max-width: 768px) {
  .prompt-templates {
    padding: 12px;
  }
  
  .page-header {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .search-bar {
    padding: 12px 16px;
  }
  
  .search-bar :deep(.el-form-item) {
    margin-right: 12px;
  }
  
  .search-bar :deep(.el-input) {
    width: 150px;
  }
  
  .search-bar :deep(.el-select) {
    width: 80px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }
  
  .action-buttons .el-button {
    width: 100%;
    justify-content: center;
  }
}
</style>
