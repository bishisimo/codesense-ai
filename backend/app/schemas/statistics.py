"""
统计数据相关的Pydantic模式
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProjectStats(BaseModel):
    """项目统计信息"""
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    total_mrs: int = Field(..., description="总MR数量")
    merged_mrs: int = Field(..., description="已合并MR数量")
    open_mrs: int = Field(..., description="打开状态MR数量")
    total_additions: int = Field(..., description="总新增行数")
    total_deletions: int = Field(..., description="总删除行数")
    net_changes: int = Field(..., description="净变化行数")
    avg_mr_size: float = Field(..., description="平均MR大小")
    review_coverage: float = Field(..., description="审查覆盖率")
    # 新增：代码增长和减少的详细指标
    code_growth_rate: float = Field(..., description="代码增长率(%)")
    code_reduction_rate: float = Field(..., description="代码减少率(%)")
    avg_additions_per_mr: float = Field(..., description="平均每个MR新增行数")
    avg_deletions_per_mr: float = Field(..., description="平均每个MR删除行数")


class UserStats(BaseModel):
    """用户统计信息"""
    author: str = Field(..., description="作者")
    total_mrs: int = Field(..., description="总MR数量")
    merged_mrs: int = Field(..., description="已合并MR数量")
    total_additions: int = Field(..., description="总新增行数")
    total_deletions: int = Field(..., description="总删除行数")
    net_changes: int = Field(..., description="净变化行数")
    avg_mr_size: float = Field(..., description="平均MR大小")
    avg_review_score: Optional[float] = Field(None, description="平均审查评分")
    total_commits: int = Field(..., description="总提交数")
    # 新增：用户代码变更详细指标
    code_growth_rate: float = Field(..., description="代码增长率(%)")
    code_reduction_rate: float = Field(..., description="代码减少率(%)")
    avg_additions_per_mr: float = Field(..., description="平均每个MR新增行数")
    avg_deletions_per_mr: float = Field(..., description="平均每个MR删除行数")
    productivity_score: float = Field(..., description="生产力评分(基于代码变更量和质量)")
    # 新增：分层生产力评分
    contribution_score: float = Field(..., description="贡献层评分(40%)")
    code_efficiency_score: float = Field(..., description="代码效率层评分(30%)")
    quality_score: float = Field(..., description="质量层评分(20%)")
    participation_score: float = Field(..., description="参与活跃层评分(10%)")


class CodeQualityTrend(BaseModel):
    """代码质量趋势"""
    date: str = Field(..., description="日期")
    avg_score: Optional[float] = Field(None, description="平均评分")
    review_count: int = Field(..., description="审查数量")
    pass_rate: float = Field(..., description="通过率")


class EfficiencyMetrics(BaseModel):
    """效率指标"""
    avg_mr_duration: float = Field(..., description="平均MR处理时间(小时)")
    avg_review_time: float = Field(..., description="平均审查时间(小时)")
    mrs_per_day: float = Field(..., description="每日MR数量")
    commits_per_day: float = Field(..., description="每日提交数")


class TechnicalDebt(BaseModel):
    """技术债务"""
    long_pending_mrs: int = Field(..., description="长期待处理MR数量")
    re_reviewed_mrs: int = Field(..., description="重复审查MR数量")
    high_risk_patterns: int = Field(..., description="高风险代码模式数量")
    oldest_pending_days: Optional[int] = Field(None, description="最老待处理MR天数")


class TokenUsageTrend(BaseModel):
    """Token使用趋势"""
    date: str = Field(..., description="日期")
    total_tokens: int = Field(..., description="总token数")
    direct_tokens: int = Field(..., description="直接token数")
    cache_tokens: int = Field(..., description="缓存token数")
    prompt_tokens: int = Field(..., description="输入token数")
    completion_tokens: int = Field(..., description="输出token数")
    cost: float = Field(..., description="成本")


class TokenUsageByModel(BaseModel):
    """按模型统计Token使用"""
    model_name: str = Field(..., description="模型名称")
    total_tokens: int = Field(..., description="总token数")
    direct_tokens: int = Field(..., description="直接token数")
    cache_tokens: int = Field(..., description="缓存token数")
    cost: float = Field(..., description="成本")
    usage_count: int = Field(..., description="使用次数")


class TokenUsageByProject(BaseModel):
    """按项目统计Token使用"""
    project_name: str = Field(..., description="项目名称")
    total_tokens: int = Field(..., description="总token数")
    direct_tokens: int = Field(..., description="直接token数")
    cache_tokens: int = Field(..., description="缓存token数")
    cost: float = Field(..., description="成本")
    review_count: int = Field(..., description="审查次数")


# 注意：StatisticsResponse 和 StatisticsRequest 已废弃
# 现在使用分接口，每个接口有自己的请求和响应格式
