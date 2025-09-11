<template>
  <div class="statistics-container">
    <!-- 页面标题和筛选器 -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">
          <el-icon class="title-icon"><TrendCharts /></el-icon>
          数据统计
        </h2>
        <div class="filters">
          <el-select v-model="timeFilter.period" placeholder="时间周期" @change="handleTimePeriodChange" style="width: 120px;">
            <el-option label="今日" value="today" />
            <el-option label="本周" value="this_week" />
            <el-option label="本月" value="this_month" />
            <el-option label="近一周" value="week" />
            <el-option label="近一月" value="month" />
            <el-option label="近一季" value="quarter" />
            <el-option label="近一年" value="year" />
            <el-option label="自定义" value="custom" />
          </el-select>
          
          <el-select v-model="timeCriteria" placeholder="时间标准" @change="handleTimeCriteriaChange" style="width: 120px;">
            <el-option label="创建时间" value="created" />
            <el-option label="更新时间" value="updated" />
            <el-option label="活动时间" value="activity" />
          </el-select>
          
          <el-date-picker
            v-if="timeFilter.period === 'custom'"
            v-model="customDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleCustomDateChange"
            style="width: 240px;"
          />
          
          <el-button type="primary" @click="loadStatistics" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 汇总卡片 -->
    <div class="summary-section" v-if="statistics">
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-icon projects-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="summary-content">
            <div class="summary-number">{{ statistics.summary.total_projects }}</div>
            <div class="summary-label">项目总数</div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon mrs-icon">
            <el-icon><DocumentCopy /></el-icon>
          </div>
          <div class="summary-content">
            <div class="summary-number">{{ statistics.summary.total_mrs }}</div>
            <div class="summary-label">MR总数</div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon coverage-icon">
            <el-icon><Check /></el-icon>
          </div>
          <div class="summary-content">
            <div class="summary-number">{{ statistics.summary.review_coverage }}%</div>
            <div class="summary-label">审查覆盖率</div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon score-icon">
            <el-icon><Star /></el-icon>
          </div>
          <div class="summary-content">
            <div class="summary-number">{{ statistics.summary.avg_review_score }}</div>
            <div class="summary-label">平均评分</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section" v-if="statistics">
      <el-row :gutter="20">
        <!-- 项目统计图表 -->
        <el-col :span="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><PieChart /></el-icon>
                  项目代码变更统计
                </span>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="openFullscreenChart('project')"
                  class="fullscreen-btn"
                  :icon="FullScreen"
                  circle
                />
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('project')">
              <div ref="projectChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 用户统计图表 -->
        <el-col :span="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><User /></el-icon>
                  用户贡献统计
                </span>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="openFullscreenChart('user')"
                  class="fullscreen-btn"
                  :icon="FullScreen"
                  circle
                />
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('user')">
              <div ref="userChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 代码质量趋势 -->
        <el-col :span="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><TrendCharts /></el-icon>
                  代码质量趋势
                </span>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="openFullscreenChart('quality')"
                  class="fullscreen-btn"
                  :icon="FullScreen"
                  circle
                />
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('quality')">
              <div ref="qualityChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 效率指标 -->
        <el-col :span="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><Timer /></el-icon>
                  开发效率指标
                </span>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="openFullscreenChart('efficiency')"
                  class="fullscreen-btn"
                  :icon="FullScreen"
                  circle
                />
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('efficiency')">
              <div ref="efficiencyChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- Token使用统计图表 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- Token使用趋势 -->
        <el-col :span="12" v-if="statistics.token_usage_trends.length > 0">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><TrendCharts /></el-icon>
                  Token使用趋势
                </span>
                <el-button 
                  type="text" 
                  @click="openFullscreenChart('token-trend')"
                  class="expand-btn"
                >
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('token-trend')">
              <div ref="tokenTrendChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 按模型统计Token使用 -->
        <el-col :span="12" v-if="statistics.token_usage_by_model.length > 0">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><Cpu /></el-icon>
                  按模型统计Token使用
                </span>
                <el-button 
                  type="text" 
                  @click="openFullscreenChart('token-model')"
                  class="expand-btn"
                >
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('token-model')">
              <div ref="tokenByModelChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 按项目统计Token使用 -->
      <el-row :gutter="20" style="margin-top: 20px;" v-if="statistics.token_usage_by_project.length > 0">
        <el-col :span="24">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><Folder /></el-icon>
                  按项目统计Token使用
                </span>
                <el-button 
                  type="text" 
                  @click="openFullscreenChart('token-project')"
                  class="expand-btn"
                >
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="chart-container" @click="openFullscreenChart('token-project')">
              <div ref="tokenByProjectChart" class="chart"></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细数据表格 -->
    <div class="tables-section" v-if="statistics">
      <el-row :gutter="20">
        <!-- 项目详细统计 -->
        <el-col :span="12">
          <el-card class="table-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><Folder /></el-icon>
                  项目详细统计
                </span>
              </div>
            </template>
            <div class="table-container">
              <el-table 
                :data="statistics.project_stats" 
                stripe 
                style="width: 100%"
                height="400"
                :scrollbar-always-on="true"
              >
                <el-table-column prop="project_name" label="项目名称" min-width="120" fixed="left" />
                <el-table-column prop="total_mrs" label="MR总数" width="100" sortable />
                <el-table-column prop="merged_mrs" label="已合并" width="90" sortable />
                <el-table-column prop="total_additions" label="新增行数" width="110" sortable default-sort="descending">
                  <template #default="{ row }">
                    <span class="positive">+{{ row.total_additions }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="total_deletions" label="删除行数" width="110" sortable>
                  <template #default="{ row }">
                    <span class="negative">-{{ row.total_deletions }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="net_changes" label="净变更" width="110" sortable>
                  <template #default="{ row }">
                    <span :class="row.net_changes >= 0 ? 'positive' : 'negative'">
                      {{ row.net_changes >= 0 ? '+' : '' }}{{ row.net_changes }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="code_growth_rate" label="增长率" width="90" sortable>
                  <template #default="{ row }">
                    <span class="positive">{{ row.code_growth_rate }}%</span>
                  </template>
                </el-table-column>
                <el-table-column prop="code_reduction_rate" label="减少率" width="90" sortable>
                  <template #default="{ row }">
                    <span class="negative">{{ row.code_reduction_rate }}%</span>
                  </template>
                </el-table-column>
                <el-table-column prop="review_coverage" label="审查率" width="90" sortable>
                  <template #default="{ row }">
                    {{ row.review_coverage }}%
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-col>
        
        <!-- 用户详细统计 -->
        <el-col :span="12">
          <el-card class="table-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><User /></el-icon>
                  用户详细统计
                </span>
              </div>
            </template>
            <div class="table-container">
              <el-table 
                :data="statistics.user_stats" 
                stripe 
                style="width: 100%"
                height="400"
                :scrollbar-always-on="true"
              >
                <el-table-column prop="author" label="作者" min-width="100" fixed="left" />
                <el-table-column prop="total_mrs" label="MR总数" width="100" sortable />
                <el-table-column prop="merged_mrs" label="已合并" width="90" sortable />
                <el-table-column prop="total_commits" label="提交数" width="90" sortable />
                <el-table-column prop="total_additions" label="新增" width="90" sortable default-sort="descending">
                  <template #default="{ row }">
                    <span class="positive">+{{ row.total_additions }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="total_deletions" label="删除" width="90" sortable>
                  <template #default="{ row }">
                    <span class="negative">-{{ row.total_deletions }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="net_changes" label="净变更" width="110" sortable>
                  <template #default="{ row }">
                    <span :class="row.net_changes >= 0 ? 'positive' : 'negative'">
                      {{ row.net_changes >= 0 ? '+' : '' }}{{ row.net_changes }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="avg_review_score" label="平均评分" width="110" sortable>
                  <template #default="{ row }">
                    {{ row.avg_review_score || '-' }}
                  </template>
                </el-table-column>
                <!-- 分层生产力评分 -->
                <el-table-column label="分层评分" width="200" align="center">
                  <template #default="{ row }">
                    <div class="layered-scores">
                      <div class="score-item">
                        <span class="score-label">贡献</span>
                        <span class="score-value" :class="getScoreClass(row.contribution_score)">{{ row.contribution_score }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">效率</span>
                        <span class="score-value" :class="getScoreClass(row.code_efficiency_score)">{{ row.code_efficiency_score }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">质量</span>
                        <span class="score-value" :class="getScoreClass(row.quality_score)">{{ row.quality_score }}</span>
                      </div>
                      <div class="score-item">
                        <span class="score-label">活跃</span>
                        <span class="score-value" :class="getScoreClass(row.participation_score)">{{ row.participation_score }}</span>
                      </div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="productivity_score" label="生产力" width="90" sortable>
                  <template #default="{ row }">
                    <span :class="row.productivity_score >= 70 ? 'positive' : row.productivity_score >= 50 ? 'warning' : 'negative'">
                      {{ row.productivity_score }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 技术债务提醒 -->
    <div class="debt-section" v-if="statistics && statistics.technical_debt">
      <el-card class="debt-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Warning /></el-icon>
              技术债务监控
            </span>
          </div>
        </template>
        <div class="debt-grid">
          <div class="debt-item">
            <div class="debt-number">{{ statistics.technical_debt.long_pending_mrs }}</div>
            <div class="debt-label">长期待处理MR</div>
          </div>
          <div class="debt-item">
            <div class="debt-number">{{ statistics.technical_debt.oldest_pending_days || 0 }}</div>
            <div class="debt-label">最老待处理天数</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 全屏图表弹窗 -->
    <el-dialog
      v-model="fullscreenDialogVisible"
      :title="fullscreenChartTitle"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      class="fullscreen-chart-dialog"
    >
      <div class="fullscreen-chart-container">
        <div ref="fullscreenChart" class="fullscreen-chart"></div>
      </div>
      
      <!-- 详细数据表格 -->
      <div class="fullscreen-data-table" v-if="fullscreenChartData">
        <el-table :data="fullscreenChartData" stripe style="width: 100%">
          <el-table-column 
            v-for="column in fullscreenTableColumns" 
            :key="column.prop"
            :prop="column.prop" 
            :label="column.label" 
            :width="column.width"
            :formatter="column.formatter"
          />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  TrendCharts, 
  Refresh, 
  Folder, 
  DocumentCopy, 
  Check, 
  Star, 
  PieChart, 
  User, 
  Timer, 
  Warning,
  FullScreen
} from '@element-plus/icons-vue'
import { combinedStatsApi, type StatisticsResponse, type TimeRangeFilter } from '@/api/statistics'

// 定义组件名称
defineOptions({
  name: 'StatisticsPage'
})

// 响应式数据
const loading = ref(false)
const statistics = ref<StatisticsResponse | null>(null)
const timeFilter = ref<TimeRangeFilter>({ period: 'this_month' })
const customDateRange = ref<[string, string] | null>(null)
const timeCriteria = ref<'created' | 'updated' | 'activity'>('activity')

// 图表引用
const projectChart = ref<HTMLElement>()
const userChart = ref<HTMLElement>()
const qualityChart = ref<HTMLElement>()
const efficiencyChart = ref<HTMLElement>()
const tokenTrendChart = ref<HTMLElement>()
const tokenByModelChart = ref<HTMLElement>()
const tokenByProjectChart = ref<HTMLElement>()

// 全屏弹窗相关
const fullscreenDialogVisible = ref(false)
const fullscreenChartTitle = ref('')
const fullscreenChart = ref<HTMLElement>()
const fullscreenChartData = ref<any[]>([])
const fullscreenTableColumns = ref<any[]>([])
const currentChartType = ref('')

// 恢复echarts导入
import * as echarts from 'echarts'

// 全局配置ECharts使用passive事件监听器
echarts.registerTheme('passive', {
  animation: true,
  animationDuration: 1000,
  animationEasing: 'cubicOut'
})

// 配置passive事件监听器（仅在组件内生效）
const setupPassiveEventListeners = () => {
  // 为ECharts容器添加passive事件监听器配置
  const originalAddEventListener = EventTarget.prototype.addEventListener
  EventTarget.prototype.addEventListener = function(type, listener, options) {
    if (type === 'mousewheel' || type === 'wheel' || type === 'touchstart' || type === 'touchmove') {
      if (typeof options === 'boolean') {
        options = { capture: options, passive: true }
      } else if (typeof options === 'object') {
        options = { ...options, passive: true }
      } else {
        options = { passive: true }
      }
    }
    return originalAddEventListener.call(this, type, listener, options)
  }
}

// 创建图表实例的通用函数
const createChart = (container: HTMLElement, option: any) => {
  const chart = echarts.init(container, 'passive', {
    useDirtyRect: true,
    renderer: 'canvas'
  })
  
  chart.setOption(option)
  return chart
}

// 获取分数样式类
const getScoreClass = (score: number) => {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-average'
  return 'score-poor'
}

// 组件挂载时设置passive事件监听器
onMounted(() => {
  setupPassiveEventListeners()
})

// 加载统计数据
const loadStatistics = async () => {
  try {
    loading.value = true
    console.log('开始加载统计数据...')
    
    const params: any = {
      period: timeFilter.value.period,
      time_criteria: timeCriteria.value,
      days: 30
    }
    
    // 如果是自定义时间范围，添加日期参数
    if (timeFilter.value.period === 'custom' && customDateRange.value) {
      params.start_date = customDateRange.value[0]
      params.end_date = customDateRange.value[1]
    }
    
    console.log('发送请求:', params)
    const response = await combinedStatsApi.getAllStatistics(params)
    statistics.value = response as any
    console.log('收到响应:', statistics.value)
    
    // 等待DOM更新后渲染图表
    await nextTick()
    renderCharts()
    
  } catch (error) {
    ElMessage.error('加载统计数据失败')
    console.error('Statistics loading error:', error)
    console.error('Error details:', error)
  } finally {
    loading.value = false
  }
}

// 处理时间周期变化
const handleTimePeriodChange = () => {
  if (timeFilter.value.period !== 'custom') {
    customDateRange.value = null
  }
  loadStatistics()
}

// 处理自定义日期变化
const handleCustomDateChange = () => {
  if (customDateRange.value) {
    loadStatistics()
  }
}

// 处理时间标准变化
const handleTimeCriteriaChange = () => {
  loadStatistics()
}

// 渲染图表
const renderCharts = () => {
  if (!statistics.value) return
  
  // 使用nextTick确保DOM已更新
  nextTick(() => {
    try {
      renderProjectChart()
      renderUserChart()
      renderQualityChart()
      renderEfficiencyChart()
      renderTokenTrendChart()
      renderTokenByModelChart()
      renderTokenByProjectChart()
    } catch (error) {
      console.warn('图表渲染过程中出现错误:', error)
    }
  })
}

// 渲染项目统计图表
const renderProjectChart = () => {
  if (!projectChart.value || !statistics.value) return
  
  try {
    const option = getProjectChartOption(false)
    createChart(projectChart.value, option)
  } catch (error) {
    console.warn('项目图表渲染失败:', error)
  }
}

// 渲染用户统计图表
const renderUserChart = () => {
  if (!userChart.value || !statistics.value) return
  
  try {
    const option = getUserChartOption(false)
    createChart(userChart.value, option)
  } catch (error) {
    console.warn('用户图表渲染失败:', error)
  }
}

// 渲染代码质量趋势图表
const renderQualityChart = () => {
  if (!qualityChart.value || !statistics.value) return
  
  try {
    const option = getQualityChartOption(false)
    createChart(qualityChart.value, option)
  } catch (error) {
    console.warn('质量图表渲染失败:', error)
  }
}

// 渲染效率指标图表
const renderEfficiencyChart = () => {
  if (!efficiencyChart.value || !statistics.value) return
  
  try {
    const option = getEfficiencyChartOption(false)
    createChart(efficiencyChart.value, option)
  } catch (error) {
    console.warn('效率图表渲染失败:', error)
  }
}

// 渲染Token使用趋势图表
const renderTokenTrendChart = () => {
  if (!tokenTrendChart.value || !statistics.value) return
  
  try {
    const option = getTokenTrendChartOption(false)
    createChart(tokenTrendChart.value, option)
  } catch (error) {
    console.warn('Token趋势图表渲染失败:', error)
  }
}

// 渲染按模型统计Token使用图表
const renderTokenByModelChart = () => {
  if (!tokenByModelChart.value || !statistics.value) return
  
  try {
    const option = getTokenByModelChartOption(false)
    createChart(tokenByModelChart.value, option)
  } catch (error) {
    console.warn('Token模型图表渲染失败:', error)
  }
}

// 渲染按项目统计Token使用图表
const renderTokenByProjectChart = () => {
  if (!tokenByProjectChart.value || !statistics.value) return
  
  try {
    const option = getTokenByProjectChartOption(false)
    createChart(tokenByProjectChart.value, option)
  } catch (error) {
    console.warn('Token项目图表渲染失败:', error)
  }
}

// 打开全屏图表
const openFullscreenChart = (chartType: string) => {
  if (!statistics.value) return
  
  try {
    currentChartType.value = chartType
    fullscreenDialogVisible.value = true
  
  // 设置标题和数据
  switch (chartType) {
    case 'project':
      fullscreenChartTitle.value = '项目代码变更统计 - 详细数据'
      fullscreenChartData.value = statistics.value.project_stats
      fullscreenTableColumns.value = [
        { prop: 'project_name', label: '项目名称', width: 150 },
        { prop: 'total_mrs', label: 'MR总数', width: 100 },
        { prop: 'merged_mrs', label: '已合并', width: 100 },
        { prop: 'total_additions', label: '新增行数', width: 120, formatter: (row: any) => `+${row.total_additions}` },
        { prop: 'total_deletions', label: '删除行数', width: 120, formatter: (row: any) => `-${row.total_deletions}` },
        { prop: 'net_changes', label: '净变更', width: 120, formatter: (row: any) => `${row.net_changes >= 0 ? '+' : ''}${row.net_changes}` },
        { prop: 'review_coverage', label: '审查率', width: 100, formatter: (row: any) => `${row.review_coverage}%` },
        { prop: 'code_growth_rate', label: '增长率', width: 100, formatter: (row: any) => `${row.code_growth_rate}%` },
        { prop: 'code_reduction_rate', label: '减少率', width: 100, formatter: (row: any) => `${row.code_reduction_rate}%` }
      ]
      break
    case 'user':
      fullscreenChartTitle.value = '用户贡献统计 - 详细数据'
      fullscreenChartData.value = statistics.value.user_stats
      fullscreenTableColumns.value = [
        { prop: 'author', label: '作者', width: 120 },
        { prop: 'total_mrs', label: 'MR数', width: 80 },
        { prop: 'merged_mrs', label: '已合并', width: 80 },
        { prop: 'total_commits', label: '提交数', width: 100 },
        { prop: 'total_additions', label: '新增', width: 100, formatter: (row: any) => `+${row.total_additions}` },
        { prop: 'total_deletions', label: '删除', width: 100, formatter: (row: any) => `-${row.total_deletions}` },
        { prop: 'net_changes', label: '净变更', width: 120, formatter: (row: any) => `${row.net_changes >= 0 ? '+' : ''}${row.net_changes}` },
        { prop: 'avg_review_score', label: '平均评分', width: 100, formatter: (row: any) => row.avg_review_score || '-' },
        { prop: 'code_growth_rate', label: '增长率', width: 100, formatter: (row: any) => `${row.code_growth_rate}%` },
        { prop: 'contribution_score', label: '贡献层', width: 80, formatter: (row: any) => `${row.contribution_score}` },
        { prop: 'code_efficiency_score', label: '效率层', width: 80, formatter: (row: any) => `${row.code_efficiency_score}` },
        { prop: 'quality_score', label: '质量层', width: 80, formatter: (row: any) => `${row.quality_score}` },
        { prop: 'participation_score', label: '活跃层', width: 80, formatter: (row: any) => `${row.participation_score}` },
        { prop: 'productivity_score', label: '生产力', width: 100, formatter: (row: any) => `${row.productivity_score}` }
      ]
      break
    case 'quality':
      fullscreenChartTitle.value = '代码质量趋势 - 详细数据'
      fullscreenChartData.value = statistics.value.quality_trends
      fullscreenTableColumns.value = [
        { prop: 'date', label: '时间', width: 120 },
        { prop: 'avg_score', label: '平均评分', width: 100, formatter: (row: any) => row.avg_score || '-' },
        { prop: 'review_count', label: '审查数量', width: 100 },
        { prop: 'pass_rate', label: '通过率', width: 100, formatter: (row: any) => `${row.pass_rate}%` }
      ]
      break
    case 'efficiency':
      fullscreenChartTitle.value = '开发效率指标 - 详细数据'
      const efficiencyData = [{
        metric: '平均MR时长(小时)',
        value: statistics.value.efficiency_metrics.avg_mr_duration
      }, {
        metric: '平均审查时间(小时)',
        value: statistics.value.efficiency_metrics.avg_review_time
      }, {
        metric: '每日MR数',
        value: statistics.value.efficiency_metrics.mrs_per_day
      }, {
        metric: '每日提交数',
        value: statistics.value.efficiency_metrics.commits_per_day
      }]
      fullscreenChartData.value = efficiencyData
      fullscreenTableColumns.value = [
        { prop: 'metric', label: '指标', width: 200 },
        { prop: 'value', label: '数值', width: 150, formatter: (row: any) => row.value.toFixed(2) }
      ]
      break
    case 'token-trend':
      fullscreenChartTitle.value = 'Token使用趋势 - 详细数据'
      fullscreenChartData.value = statistics.value.token_usage_trends
      fullscreenTableColumns.value = [
        { prop: 'date', label: '日期', width: 120 },
        { prop: 'total_tokens', label: '总Token', width: 120 },
        { prop: 'direct_tokens', label: '直接Token', width: 120 },
        { prop: 'cache_tokens', label: '缓存Token', width: 120 },
        { prop: 'prompt_tokens', label: '输入Token', width: 120 },
        { prop: 'completion_tokens', label: '输出Token', width: 120 },
        { prop: 'cost', label: '成本($)', width: 100, formatter: (row: any) => row.cost.toFixed(4) }
      ]
      break
    case 'token-model':
      fullscreenChartTitle.value = '按模型统计Token使用 - 详细数据'
      fullscreenChartData.value = statistics.value.token_usage_by_model
      fullscreenTableColumns.value = [
        { prop: 'model_name', label: '模型名称', width: 150 },
        { prop: 'total_tokens', label: '总Token', width: 120 },
        { prop: 'direct_tokens', label: '直接Token', width: 120 },
        { prop: 'cache_tokens', label: '缓存Token', width: 120 },
        { prop: 'cost', label: '成本($)', width: 100, formatter: (row: any) => row.cost.toFixed(4) },
        { prop: 'usage_count', label: '使用次数', width: 100 }
      ]
      break
    case 'token-project':
      fullscreenChartTitle.value = '按项目统计Token使用 - 详细数据'
      fullscreenChartData.value = statistics.value.token_usage_by_project
      fullscreenTableColumns.value = [
        { prop: 'project_name', label: '项目名称', width: 150 },
        { prop: 'total_tokens', label: '总Token', width: 120 },
        { prop: 'direct_tokens', label: '直接Token', width: 120 },
        { prop: 'cache_tokens', label: '缓存Token', width: 120 },
        { prop: 'cost', label: '成本($)', width: 100, formatter: (row: any) => row.cost.toFixed(4) },
        { prop: 'review_count', label: '审查次数', width: 100 }
      ]
      break
  }
  
    // 等待DOM更新后渲染全屏图表
    nextTick(() => {
      renderFullscreenChart()
    })
  } catch (error) {
    console.warn('打开全屏图表失败:', error)
  }
}

// 渲染全屏图表
const renderFullscreenChart = () => {
  if (!fullscreenChart.value || !statistics.value) return
  
  try {
    const chart = echarts.init(fullscreenChart.value, 'passive', {
      useDirtyRect: true,
      renderer: 'canvas'
    })
  
  let option: any = {}
  
  switch (currentChartType.value) {
    case 'project':
      option = getProjectChartOption(true)
      break
    case 'user':
      option = getUserChartOption(true)
      break
    case 'quality':
      option = getQualityChartOption(true)
      break
    case 'efficiency':
      option = getEfficiencyChartOption(true)
      break
    case 'token-trend':
      option = getTokenTrendChartOption(true)
      break
    case 'token-model':
      option = getTokenByModelChartOption(true)
      break
    case 'token-project':
      option = getTokenByProjectChartOption(true)
      break
  }
  
    chart.setOption(option)
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
      chart.resize()
    })
  } catch (error) {
    console.warn('全屏图表渲染失败:', error)
  }
}

// 获取项目图表配置
const getProjectChartOption = (isFullscreen = false) => {
  const categories = statistics.value!.project_stats.map(p => p.project_name)
  const additionsData = statistics.value!.project_stats.map(p => p.total_additions)
  const deletionsData = statistics.value!.project_stats.map(p => -p.total_deletions)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params: any) {
        let result = params[0].name + '<br/>'
        params.forEach((param: any) => {
          const value = param.seriesName === '删除行数' ? -param.value : param.value
          result += param.marker + param.seriesName + ': ' + value + '<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['新增行数', '删除行数'],
      top: isFullscreen ? 20 : 10
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        rotate: isFullscreen ? 0 : 45,
        interval: isFullscreen ? 0 : 'auto'
      }
    },
    yAxis: {
      type: 'value',
      name: '代码行数'
    },
    series: [
      {
        name: '新增行数',
        type: 'bar',
        data: additionsData,
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '删除行数',
        type: 'bar',
        data: deletionsData,
        itemStyle: { color: '#f56c6c' }
      }
    ]
  }
}

// 获取用户图表配置
const getUserChartOption = (isFullscreen = false) => {
  const data = statistics.value!.user_stats.slice(0, isFullscreen ? 20 : 10)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params: any) {
        let result = params[0].name + '<br/>'
        params.forEach((param: any) => {
          const value = param.seriesName === '删除行数' ? -param.value : param.value
          result += param.marker + param.seriesName + ': ' + value + '<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['新增行数', '删除行数', '生产力评分'],
      top: isFullscreen ? 20 : 10
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(u => u.author),
      axisLabel: {
        rotate: isFullscreen ? 0 : 45,
        interval: isFullscreen ? 0 : 'auto'
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '代码行数',
        position: 'left'
      },
      {
        type: 'value',
        name: '生产力评分',
        position: 'right',
        max: 100
      }
    ],
    series: [
      {
        name: '新增行数',
        type: 'bar',
        yAxisIndex: 0,
        data: data.map(u => u.total_additions),
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '删除行数',
        type: 'bar',
        yAxisIndex: 0,
        data: data.map(u => -u.total_deletions),
        itemStyle: { color: '#f56c6c' }
      },
      {
        name: '生产力评分',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(u => u.productivity_score),
        itemStyle: { color: '#e6a23c' },
        lineStyle: { color: '#e6a23c' }
      }
    ]
  }
}

// 获取质量趋势图表配置
const getQualityChartOption = (isFullscreen = false) => {
  const data = statistics.value!.quality_trends
  
  return {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['平均评分', '通过率'],
      top: isFullscreen ? 20 : 10
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date)
    },
    yAxis: [
      {
        type: 'value',
        name: '平均评分',
        position: 'left'
      },
      {
        type: 'value',
        name: '通过率(%)',
        position: 'right'
      }
    ],
    series: [
      {
        name: '平均评分',
        type: 'line',
        yAxisIndex: 0,
        data: data.map(d => d.avg_score || 0),
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '通过率',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(d => d.pass_rate),
        itemStyle: {
          color: '#e6a23c'
        }
      }
    ]
  }
}

// 获取效率指标图表配置
const getEfficiencyChartOption = (isFullscreen = false) => {
  const metrics = statistics.value!.efficiency_metrics
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['平均MR时长(小时)', '平均审查时间(小时)', '每日MR数', '每日提交数']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '效率指标',
        type: 'bar',
        data: [
          metrics.avg_mr_duration,
          metrics.avg_review_time,
          metrics.mrs_per_day,
          metrics.commits_per_day
        ],
        itemStyle: {
          color: function(params: any) {
            const colors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a']
            return colors[params.dataIndex]
          }
        }
      }
    ]
  }
}

// 获取Token使用趋势图表配置
const getTokenTrendChartOption = (isFullscreen = false) => {
  const trends = statistics.value!.token_usage_trends
  const dates = trends.map(t => t.date)
  const totalTokens = trends.map(t => t.total_tokens)
  const directTokens = trends.map(t => t.direct_tokens)
  const cacheTokens = trends.map(t => t.cache_tokens)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['总Token', '直接Token', '缓存Token']
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: 'Token数量'
    },
    series: [
      {
        name: '总Token',
        type: 'line',
        data: totalTokens,
        smooth: true,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '直接Token',
        type: 'line',
        data: directTokens,
        smooth: true,
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '缓存Token',
        type: 'line',
        data: cacheTokens,
        smooth: true,
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }
}

// 获取按模型统计Token使用图表配置
const getTokenByModelChartOption = (isFullscreen = false) => {
  const models = statistics.value!.token_usage_by_model
  const modelNames = models.map(m => m.model_name)
  const totalTokens = models.map(m => m.total_tokens)
  const costs = models.map(m => m.cost)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['Token使用量', '成本($)']
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: modelNames,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Token数量',
        position: 'left'
      },
      {
        type: 'value',
        name: '成本($)',
        position: 'right'
      }
    ],
    series: [
      {
        name: 'Token使用量',
        type: 'bar',
        data: totalTokens,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '成本($)',
        type: 'line',
        yAxisIndex: 1,
        data: costs,
        itemStyle: { color: '#f56c6c' }
      }
    ]
  }
}

// 获取按项目统计Token使用图表配置
const getTokenByProjectChartOption = (isFullscreen = false) => {
  const projects = statistics.value!.token_usage_by_project
  const projectNames = projects.map(p => p.project_name)
  const totalTokens = projects.map(p => p.total_tokens)
  const directTokens = projects.map(p => p.direct_tokens)
  const cacheTokens = projects.map(p => p.cache_tokens)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['总Token', '直接Token', '缓存Token']
    },
    grid: {
      left: isFullscreen ? '5%' : '3%',
      right: isFullscreen ? '5%' : '4%',
      bottom: isFullscreen ? '15%' : '10%',
      top: isFullscreen ? '15%' : '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: projectNames,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: 'Token数量'
    },
    series: [
      {
        name: '总Token',
        type: 'bar',
        stack: 'total',
        data: totalTokens,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '直接Token',
        type: 'bar',
        stack: 'total',
        data: directTokens,
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '缓存Token',
        type: 'bar',
        stack: 'total',
        data: cacheTokens,
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.title-icon {
  font-size: 28px;
  color: #409eff;
}

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.summary-section {
  margin-bottom: 20px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 10px;
  font-size: 20px;
  color: white;
}

.projects-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.mrs-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.coverage-icon {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.score-icon {
  background: linear-gradient(135deg, #ffd93d, #ff6b6b);
}

.summary-content {
  flex: 1;
}

.summary-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card, .table-card, .debt-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-container {
  height: 300px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.chart-container:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart {
  width: 100%;
  height: 100%;
}

.fullscreen-btn {
  margin-left: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.tables-section {
  margin-bottom: 20px;
}

.table-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.table-container .el-table {
  border: none;
}

.table-container .el-table__header-wrapper {
  background: #f5f7fa;
}

.table-container .el-table th {
  background: #f5f7fa !important;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
}

.table-container .el-table td {
  border-bottom: 1px solid #f0f0f0;
}

.table-container .el-table__body tr:hover > td {
  background-color: #f5f7fa !important;
}

/* 优化排序图标显示 */
.table-container .el-table th {
  white-space: nowrap !important;
  overflow: visible !important;
}

.table-container .el-table .cell {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  white-space: nowrap !important;
  overflow: visible !important;
}

.table-container .el-table .el-table__column-sort {
  margin-left: 4px !important;
  flex-shrink: 0 !important;
}

.table-container .el-table .el-table__column-sort .el-icon {
  font-size: 14px !important;
}

/* 确保表头内容不换行 */
.table-container .el-table th .cell {
  padding-right: 8px !important;
}

/* 特别针对MR总数和平均评分列，确保不换行 */
.table-container .el-table th[class*="total_mrs"] .cell,
.table-container .el-table th[class*="avg_review_score"] .cell {
  min-width: 100px !important;
  white-space: nowrap !important;
  overflow: visible !important;
}

/* 确保所有表头单元格内容不换行 */
.table-container .el-table th .cell > span {
  white-space: nowrap !important;
  display: inline-block !important;
}

.debt-section {
  margin-bottom: 20px;
}

.debt-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.debt-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.debt-number {
  font-size: 32px;
  font-weight: 700;
  color: #f56c6c;
  margin-bottom: 8px;
}

.debt-label {
  font-size: 14px;
  color: #909399;
}

.positive {
  color: #67c23a;
  font-weight: 600;
}

.negative {
  color: #f56c6c;
  font-weight: 600;
}

.warning {
  color: #e6a23c;
  font-weight: 600;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-table) {
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .debt-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .statistics-container {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filters {
    width: 100%;
    justify-content: flex-start;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .debt-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .page-title {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .statistics-container {
    padding: 12px;
  }
  
  .summary-card {
    padding: 16px;
  }
  
  .summary-icon {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
  
  .summary-number {
    font-size: 24px;
  }
  
  .chart-container {
    height: 200px;
  }
}

/* 全屏图表弹窗样式 */
:deep(.fullscreen-chart-dialog) {
  .el-dialog__body {
    padding: 20px;
  }
}

.fullscreen-chart-container {
  height: 60vh;
  margin-bottom: 20px;
}

.fullscreen-chart {
  width: 100%;
  height: 100%;
}

.fullscreen-data-table {
  margin-top: 20px;
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.fullscreen-data-table .el-table {
  font-size: 14px;
}

.fullscreen-data-table .el-table th {
  background-color: #f5f7fa;
  font-weight: 600;
}

.fullscreen-data-table .el-table td {
  padding: 12px 0;
}

/* 响应式全屏弹窗 */
@media (max-width: 768px) {
  :deep(.fullscreen-chart-dialog) {
    width: 95% !important;
    top: 2vh !important;
  }
  
  .fullscreen-chart-container {
    height: 50vh;
  }
  
  .fullscreen-data-table .el-table {
    font-size: 12px;
  }
}

/* 分层评分样式 */
.layered-scores {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  line-height: 1.2;
}

.score-label {
  color: #666;
  font-weight: 500;
  min-width: 24px;
  text-align: right;
}

.score-value {
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  min-width: 32px;
  text-align: center;
  font-size: 11px;
}

.score-excellent {
  background-color: #f0f9ff;
  color: #0369a1;
  border: 1px solid #bae6fd;
}

.score-good {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.score-average {
  background-color: #fffbeb;
  color: #d97706;
  border: 1px solid #fed7aa;
}

.score-poor {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

/* 响应式分层评分 */
@media (max-width: 768px) {
  .layered-scores {
    gap: 2px;
  }
  
  .score-item {
    gap: 4px;
    font-size: 11px;
  }
  
  .score-label {
    min-width: 20px;
    font-size: 10px;
  }
  
  .score-value {
    min-width: 28px;
    font-size: 10px;
    padding: 1px 4px;
  }
}
</style>