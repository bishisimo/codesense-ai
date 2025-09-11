"""
Prompt渲染器和结果解析器实现 - 简化版本
"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from jinja2 import Environment, Template, StrictUndefined, TemplateError

from app.core.logging import get_logger
from app.services.review.ai_interfaces import (
    PromptRendererInterface, ResultParserInterface, 
    PromptTemplate, ContextInfo, ReviewResult
)
from app.services.review_template.template_variables import TemplateVariables

logger = get_logger("prompt_renderer")


class Jinja2PromptRenderer(PromptRendererInterface):
    """基于Jinja2的Prompt渲染器 - 简化版本"""
    
    def __init__(self):
        self.env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False
        )
        self.template_variables = TemplateVariables()
    
    def render_prompt(self, template: PromptTemplate, context: ContextInfo, code_diff: str) -> str:
        """渲染Prompt - 简化版本"""
        try:
            # 构建渲染数据
            render_data = self._build_render_data(context, code_diff)
            
            # 使用Jinja2渲染模板
            jinja_template = self.env.from_string(template.content)
            rendered_prompt = jinja_template.render(**render_data)
            
            # 如果有自定义指令，添加到渲染后的prompt中
            if context.custom_instructions:
                custom_section = f"\n\n# 自定义审查指令\n\n{context.custom_instructions}\n"
                rendered_prompt += custom_section
                logger.info(f"添加自定义审查指令到prompt，指令长度: {len(context.custom_instructions)} 字符")
            
            logger.debug(f"模板渲染成功，长度: {len(rendered_prompt)}")
            return rendered_prompt
            
        except TemplateError as e:
            logger.error(f"模板渲染失败: {str(e)}")
            raise ValueError(f"模板渲染失败: {str(e)}")
        except Exception as e:
            logger.error(f"模板渲染异常: {str(e)}")
            raise ValueError(f"模板渲染异常: {str(e)}")
    
    def validate_template(self, template: PromptTemplate) -> bool:
        """验证模板 - 简化版本，只进行基本语法检查"""
        try:
            # 基本语法验证
            self.env.from_string(template.content)
            return True
        except TemplateError as e:
            logger.warning(f"模板语法验证失败: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"模板验证异常: {str(e)}")
            return False
    
    def _build_render_data(self, context: ContextInfo, code_diff: str) -> Dict[str, Any]:
        """构建渲染数据"""
        return {
            "code_diff": code_diff,
            "project_name": context.project_name or "未知项目",
            "mr_title": context.mr_title or "未知标题",
            "source_branch": context.source_branch or "未知分支",
            "target_branch": context.target_branch or "未知目标",
            "commits_count": context.commits_count or 0,
            "changes_count": context.changes_count or 0,
            "additions_count": context.additions_count or 0,
            "deletions_count": context.deletions_count or 0,
            "review_type": context.review_type or "standard",
            "commit_sha": context.commit_sha or "未知提交",
            "complexity_analysis": context.complexity_analysis or {},
            "commit_statistics": context.commit_statistics or {},
            "diff_info": context.diff_info or {},
        }
    
    def get_available_variables(self) -> Dict[str, str]:
        """获取可用变量列表"""
        return self.template_variables.get_variables_dict()


class AIResultParser(ResultParserInterface):
    """AI结果解析器 - 简化版本"""
    
    def parse_response(self, ai_response: str, expected_format: Dict[str, Any] = None) -> ReviewResult:
        """解析AI响应 - 简化版本"""
        try:
            # 智能JSON提取
            json_data = self._extract_json(ai_response)
            logger.debug("JSON提取成功")
            
            # 验证和清理数据
            validated_data = self._validate_and_clean_data(json_data)
            logger.debug("数据验证和清理成功")
            
            # 构建ReviewResult对象
            result = self._build_review_result(validated_data)
            logger.debug("ReviewResult对象构建成功")
            
            logger.info(f"AI响应解析成功，评分: {result.score}")
            return result
            
        except Exception as e:
            logger.error(f"结果解析失败: {str(e)}")
            logger.error(f"原始AI响应内容: {ai_response}")  # 记录前500字符用于调试
            
            # 解析失败时，创建一个包含原始响应的结果对象
            # 注意：这里不设置token信息，因为token信息会在AI审查器层面添加
            return ReviewResult(
                score=0,  # 解析失败时设置为0分
                level="critical",
                summary=f"AI响应解析失败: {str(e)}",
                categories=[],
                issues=[],
                review_content=f"# AI响应解析失败\n\n**错误信息**: {str(e)}\n\n**原始响应**:\n```\n{ai_response}\n```",
                error_message=str(e),
                # 不设置token信息，让AI审查器层面处理
                tokens_used=0,
                direct_token=0,
                cache_token=0,
                prompt_token=0,
                completion_token=0,
                model_used="",
                request_duration=None  # 解析失败时无法获取请求时间
            )
    
    def validate_result(self, result: ReviewResult) -> bool:
        """验证解析结果 - 支持新格式和旧格式"""
        try:
            # 基本验证：检查必需字段
            if not hasattr(result, 'score') or result.score is None:
                logger.warning("缺少评分字段")
                return False
            
            if not hasattr(result, 'summary') or not result.summary:
                logger.warning("缺少总结字段")
                return False
            
            # 验证评分范围
            if not isinstance(result.score, (int, float)) or result.score < 0 or result.score > 100:
                logger.warning(f"评分超出有效范围: {result.score}")
                return False
            
            # 检查总结是否包含错误信息 - 这是真正的审查失败原因
            if "AI响应解析失败" in result.summary:
                logger.warning(f"审查失败：总结中包含错误信息: {result.summary}")
                return False
            
            # 验证新格式字段（如果存在）
            if hasattr(result, 'level') and result.level:
                valid_levels = ["low", "medium", "high", "critical"]
                if result.level not in valid_levels:
                    logger.warning(f"无效的审查级别: {result.level}")
                    return False
            
            # 检查问题列表是否为空（这通常表示审查失败）
            if hasattr(result, 'issues') and (not result.issues or len(result.issues) == 0):
                logger.warning("审查失败：没有发现任何问题，这通常表示审查过程异常")
                return False
            
            if hasattr(result, 'categories') and result.categories:
                # 验证categories格式
                for i, category in enumerate(result.categories):
                    if not isinstance(category, dict):
                        logger.warning(f"分类 {i} 格式无效")
                        return False
                    
                    required_fields = ["name", "score", "level", "description"]
                    for field in required_fields:
                        if field not in category:
                            logger.warning(f"分类 {i} 缺少必需字段: {field}")
                            return False
                    
                    # 验证分类评分
                    cat_score = category.get("score", 0)
                    if not isinstance(cat_score, (int, float)) or cat_score < 0 or cat_score > 100:
                        logger.warning(f"分类 {i} 评分超出范围: {cat_score}")
                        return False
                    
                    # 验证分类级别
                    cat_level = category.get("level", "")
                    if cat_level not in ["low", "medium", "high", "critical"]:
                        logger.warning(f"分类 {i} 级别无效: {cat_level}")
                        return False
            
            # 验证旧格式字段（向后兼容）
            if hasattr(result, 'score_details') and result.score_details:
                for dimension, detail in result.score_details.items():
                    if isinstance(detail, dict):
                        detail_score = detail.get('score', 0)
                        if not isinstance(detail_score, (int, float)) or detail_score < 0 or detail_score > 100:
                            logger.warning(f"维度 {dimension} 评分超出范围: {detail_score}")
                            return False
            
            logger.info("结果验证通过")
            return True
            
        except Exception as e:
            logger.error(f"结果验证异常: {str(e)}")
            return False
    
    def _extract_json(self, ai_response: str) -> Dict[str, Any]:
        """JSON提取"""
        
        # 策略1: 尝试直接解析整个响应（最优先）
        try:
            ai_response=ai_response.strip().lstrip("```json").rstrip("```").strip()  # 移除可能的代码块标记
            return json.loads(ai_response)
        except json.JSONDecodeError:
            logger.debug("直接解析整个响应失败")
            raise ValueError("无法解析AI响应为有效的JSON格式")

    
    def _clean_response_for_json(self, response: str) -> str:
        """清理响应内容，提取可能的JSON部分"""
        # 移除Markdown标记
        cleaned = re.sub(r'^#+\s*', '', response, flags=re.MULTILINE)
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
        
        # 查找可能的JSON开始和结束
        start_match = re.search(r'\{', cleaned)
        end_match = re.search(r'\}(?=\s*$)', cleaned)
        
        if start_match and end_match:
            start_pos = start_match.start()
            end_pos = end_match.end()
            return cleaned[start_pos:end_pos]
        
        return cleaned
    
    def _build_markdown_review(self, validated_data: Dict[str, Any]) -> str:
        """构建Markdown格式的审查报告"""
        try:
            markdown_parts = []
            
            # 标题
            markdown_parts.append("# 代码审查报告")
            
            # 总体评分
            score = validated_data.get("score", 0)
            level = validated_data.get("level", "medium")
            summary = validated_data.get("summary", "未提供总结")
            
            markdown_parts.append(f"## 总体评分: {score}/100")
            markdown_parts.append(f"**审查级别**: {level}")
            markdown_parts.append(f"**总结**: {summary}")
            markdown_parts.append("")
            
            # 分类评分
            categories = validated_data.get("categories", [])
            if categories:
                markdown_parts.append("## 分类评分")
                for category in categories:
                    name = category.get("name", "未知分类")
                    cat_score = category.get("score", 0)
                    cat_level = category.get("level", "medium")
                    description = category.get("description", "未提供描述")
                    
                    markdown_parts.append(f"### {name}: {cat_score}/100")
                    markdown_parts.append(f"- **级别**: {cat_level}")
                    markdown_parts.append(f"- **说明**: {description}")
                    markdown_parts.append("")
            
            # 问题列表
            issues = validated_data.get("issues", [])
            if issues:
                markdown_parts.append("## 发现的问题")
                for i, issue in enumerate(issues, 1):
                    title = issue.get("title", "未提供标题")
                    severity = issue.get("severity", "medium")
                    category = issue.get("category", "代码质量")
                    description = issue.get("description", "未提供描述")
                    file_path = issue.get("file", "")
                    line = issue.get("line")
                    suggestion = issue.get("suggestion", "请根据问题描述进行相应改进")
                    
                    markdown_parts.append(f"### {i}. {title}")
                    markdown_parts.append(f"- **严重程度**: {severity}")
                    markdown_parts.append(f"- **分类**: {category}")
                    markdown_parts.append(f"- **描述**: {description}")
                    
                    if file_path:
                        file_info = f"**文件**: {file_path}"
                        if line:
                            file_info += f" (第{line}行)"
                        markdown_parts.append(f"- {file_info}")
                    
                    markdown_parts.append(f"- **建议**: {suggestion}")
                    markdown_parts.append("")
            
            # 改进建议（向后兼容）
            improvements = validated_data.get("improvements", [])
            if improvements:
                markdown_parts.append("## 改进建议")
                for improvement in improvements:
                    markdown_parts.append(f"- {improvement}")
                markdown_parts.append("")
            
            return "\n".join(markdown_parts)
            
        except Exception as e:
            logger.error(f"构建Markdown审查报告失败: {str(e)}")
            return f"构建审查报告失败: {str(e)}"
    
    def _validate_and_clean_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和清理数据 - 支持新格式和旧格式"""
        # 首先检查数据是否为空或无效
        if not json_data or not isinstance(json_data, dict):
            raise ValueError("AI响应数据为空或格式无效")
        
        # 检查关键字段是否存在
        if "score" not in json_data:
            raise ValueError("AI响应缺少评分字段")
        
        if "summary" not in json_data or not json_data["summary"]:
            raise ValueError("AI响应缺少总结字段或总结为空")
        
        cleaned_data = {}
        
        # 验证评分 - 不再提供默认值
        cleaned_data["score"] = self._validate_score(json_data["score"])
        
        # 处理新格式字段
        if 'categories' in json_data and json_data['categories']:
            # 新格式：验证categories
            cleaned_data["categories"] = self._validate_categories(json_data.get("categories", []))
            # 从categories构建score_details（向后兼容）
            cleaned_data["score_details"] = self._build_score_details_from_categories(cleaned_data["categories"])
        else:
            # 旧格式：验证score_details
            cleaned_data["score_details"] = self._validate_score_details(json_data.get("score_details", {}))
        
        # 处理新格式字段 - 不再提供默认值
        cleaned_data["level"] = json_data.get("level")
        if not cleaned_data["level"]:
            raise ValueError("AI响应缺少审查级别字段")
        
        cleaned_data["summary"] = json_data["summary"]
        
        # 验证问题列表
        cleaned_data["issues"] = self._validate_issues(json_data.get("issues", []))
        
        # 处理旧格式字段（向后兼容）
        cleaned_data["strengths"] = json_data.get("strengths", [])
        cleaned_data["improvements"] = json_data.get("improvements", [])
        
        return cleaned_data
    
    def _validate_score(self, score: Any) -> int:
        """验证评分 - 不再提供默认值，无效时抛出异常"""
        if isinstance(score, (int, float)):
            score_int = int(score)
            if 0 <= score_int <= 100:
                return score_int
        
        # 尝试从字符串中提取数字
        if isinstance(score, str):
            numbers = re.findall(r'\d+', score)
            if numbers:
                try:
                    score_int = int(numbers[0])
                    if 0 <= score_int <= 100:
                        return score_int
                except ValueError:
                    pass
        
        # 无效评分时抛出异常，不再提供默认值
        raise ValueError(f"无效的评分值: {score}，评分必须在0-100之间")
    
    def _validate_score_details(self, score_details: Dict[str, Any]) -> Dict[str, Any]:
        """验证评分详情 - 简化版本"""
        processed_details = {}
        weights = {
            "code_quality": 0.30,
            "correctness": 0.25,
            "performance": 0.20,
            "security": 0.15,
            "testing": 0.10
        }
        
        for dimension, weight in weights.items():
            if dimension in score_details:
                detail = score_details[dimension]
                if isinstance(detail, dict):
                    # 新格式：包含score和reason
                    dimension_score = detail.get("score", 0)
                    reason = detail.get("reason", "")
                    processed_details[dimension] = {
                        "score": self._validate_score(dimension_score),
                        "reason": reason or "未提供评分原因"
                    }
                else:
                    # 旧格式：直接是分数
                    dimension_score = detail
                    processed_details[dimension] = {
                        "score": self._validate_score(dimension_score),
                        "reason": "未提供评分原因"
                    }
            else:
                # 如果某个维度缺失，使用默认值
                processed_details[dimension] = {
                    "score": 60,
                    "reason": "未评估该维度"
                }
        
        return processed_details
    
    def _validate_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证分类评分 - 新格式"""
        cleaned_categories = []
        
        if not isinstance(categories, list):
            logger.warning("categories字段不是列表，使用默认分类")
            return self._get_default_categories()
        
        for i, category in enumerate(categories):
            if isinstance(category, dict):
                name = category.get("name", "")
                score = category.get("score", 60)
                level = category.get("level", "medium")
                description = category.get("description", "")
                
                # 验证评分
                validated_score = self._validate_score(score)
                
                # 验证级别
                if level not in ["low", "medium", "high", "critical"]:
                    level = "medium"
                
                cleaned_category = {
                    "name": name,
                    "score": validated_score,
                    "level": level,
                    "description": description or "未提供描述"
                }
                cleaned_categories.append(cleaned_category)
            else:
                logger.warning(f"跳过无效的分类项 {i}: {category}")
        
        # 如果没有有效的分类，使用默认分类
        if not cleaned_categories:
            return self._get_default_categories()
        
        return cleaned_categories
    
    def _build_score_details_from_categories(self, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从categories构建score_details（向后兼容）"""
        score_details = {}
        
        for category in categories:
            name = category.get("name", "")
            score = category.get("score", 60)
            description = category.get("description", "")
            
            if name == "代码质量":
                score_details["code_quality"] = {"score": score, "reason": description}
            elif name == "功能正确性":
                score_details["correctness"] = {"score": score, "reason": description}
            elif name == "性能优化":
                score_details["performance"] = {"score": score, "reason": description}
            elif name == "安全性":
                score_details["security"] = {"score": score, "reason": description}
            elif name == "测试覆盖":
                score_details["testing"] = {"score": score, "reason": description}
        
        return score_details
    
    def _get_default_categories(self) -> List[Dict[str, Any]]:
        """获取默认分类"""
        return [
            {"name": "代码质量", "score": 60, "level": "medium", "description": "使用默认评分"},
            {"name": "功能正确性", "score": 60, "level": "medium", "description": "使用默认评分"},
            {"name": "性能优化", "score": 60, "level": "medium", "description": "使用默认评分"},
            {"name": "安全性", "score": 60, "level": "medium", "description": "使用默认评分"},
            {"name": "测试覆盖", "score": 60, "level": "medium", "description": "使用默认评分"}
        ]
    
    def _validate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证问题列表 - 支持新格式和旧格式，空列表时抛出异常"""
        cleaned_issues = []
        
        if not isinstance(issues, list):
            raise ValueError("issues字段不是列表格式")
        
        # 如果问题列表为空，抛出异常而不是返回空列表
        if not issues:
            raise ValueError("AI响应中没有发现任何问题，这通常表示审查失败")
        
        for i, issue in enumerate(issues):
            if isinstance(issue, dict):
                # 处理新格式字段
                if 'id' in issue and 'title' in issue and 'description' in issue:
                    # 新格式
                    cleaned_issue = {
                        "id": issue.get("id", f"issue_{i}"),
                        "type": issue.get("type", "info"),
                        "severity": self._validate_severity(issue.get("severity", "medium")),
                        "category": issue.get("category", "代码质量"),
                        "title": issue.get("title", "未提供标题"),
                        "description": issue.get("description", "未提供描述"),
                        "file": issue.get("file", ""),
                        "line": self._parse_line_number(issue.get("line")),
                        "suggestion": issue.get("suggestion", "请根据问题描述进行相应改进")
                    }
                else:
                    # 旧格式兼容
                    cleaned_issue = {
                        "id": f"issue_{i}",
                        "type": issue.get("type", "info"),
                        "severity": "medium",
                        "category": "代码质量",
                        "title": issue.get("message", "未提供标题"),
                        "description": issue.get("message", "未提供描述"),
                        "file": issue.get("file", ""),
                        "line": self._parse_line_number(issue.get("line")),
                        "suggestion": issue.get("suggestion", "请根据问题描述进行相应改进")
                    }
                
                # 验证必需字段 - 不再跳过，而是抛出异常
                if not cleaned_issue["title"] or cleaned_issue["title"] == "未提供标题":
                    raise ValueError(f"问题 {i} 缺少标题，这是必需的字段")
                
                if not cleaned_issue["description"] or cleaned_issue["description"] == "未提供描述":
                    raise ValueError(f"问题 {i} 缺少描述，这是必需的字段")
                
                cleaned_issues.append(cleaned_issue)
            else:
                raise ValueError(f"问题项 {i} 格式无效: {issue}")
        
        # 如果所有问题都被过滤掉了，抛出异常
        if not cleaned_issues:
            raise ValueError("所有问题都缺少必需字段，审查结果无效")
        
        return cleaned_issues
    
    def _validate_severity(self, severity: str) -> str:
        """验证问题严重程度"""
        valid_severities = ["critical", "high", "medium", "low"]
        if severity in valid_severities:
            return severity
        logger.warning(f"无效的严重程度: {severity}，使用默认值medium")
        return "medium"
    
    def _parse_line_number(self, line_value) -> Optional[int]:
        """解析行号 - 简化版本"""
        if line_value is None:
            return None
        
        if isinstance(line_value, int):
            return line_value if line_value > 0 else None
        
        if isinstance(line_value, str):
            line_value = line_value.strip()
            if not line_value or line_value.lower() in ['多个', 'multiple', 'n/a', 'null', 'none', '无', '整体']:
                return None
            
            # 提取第一个数字
            numbers = re.findall(r'\d+', line_value)
            if numbers:
                try:
                    line_num = int(numbers[0])
                    return line_num if line_num > 0 else None
                except ValueError:
                    return None
        
        return None
    
    def _build_review_result(self, validated_data: Dict[str, Any]) -> ReviewResult:
        """构建ReviewResult对象 - 支持新格式和旧格式"""
        # 构建Markdown格式的审查报告
        review_content = self._build_markdown_review(validated_data)
        
        return ReviewResult(
            score=validated_data["score"],
            level=validated_data["level"],  # 不再提供默认值
            summary=validated_data["summary"],  # 不再提供默认值
            categories=validated_data.get("categories", []),  # 新格式字段
            issues=validated_data["issues"],  # 不再提供默认值
            # 向后兼容字段
            score_details=validated_data.get("score_details", {}),
            strengths=validated_data.get("strengths", []),
            improvements=validated_data.get("improvements", []),
            review_content=review_content,
            request_duration=None  # 解析层面无法获取请求时间，由AI审查器层面设置
        )
    

    
    def _extract_score_from_text(self, text: str) -> int:
        """从文本中提取评分，无法提取时抛出异常"""
        # 查找评分相关的文本
        score_patterns = [
            r'评分[：:]\s*(\d+)',
            r'得分[：:]\s*(\d+)',
            r'分数[：:]\s*(\d+)',
            r'(\d+)\s*分',
            r'(\d+)\s*points?',
            r'score[：:]\s*(\d+)'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = int(match.group(1))
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        # 无法提取评分时抛出异常，不再提供默认值
        raise ValueError(f"无法从文本中提取有效评分: {text[:200]}...")
    
    def _extract_summary_from_text(self, text: str) -> str:
        """从文本中提取总结"""
        # 查找总结相关的文本
        summary_patterns = [
            r'总结[：:]\s*(.+)',
            r'结论[：:]\s*(.+)',
            r'概要[：:]\s*(.+)',
            r'summary[：:]\s*(.+)',
            r'conclusion[：:]\s*(.+)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 10:  # 确保总结有足够长度
                    return summary[:200]  # 限制长度
        
        return "无法提取总结信息"
    


    def _get_default_score_details(self) -> Dict[str, Any]:
        """获取默认的评分详情"""
        return {
            "code_quality": {"score": 60, "reason": "降级解析，使用默认评分"},
            "correctness": {"score": 60, "reason": "降级解析，使用默认评分"},
            "performance": {"score": 60, "reason": "降级解析，使用默认评分"},
            "security": {"score": 60, "reason": "降级解析，使用默认评分"},
            "testing": {"score": 60, "reason": "降级解析，使用默认评分"}
        }
