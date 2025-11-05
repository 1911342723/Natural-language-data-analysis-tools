"""
Reviewer Agent - 审稿人Agent
负责审核论文质量，提出修改建议
"""
import logging
from typing import Dict, Any, List

from multi_agent.base_agent import BaseAgent, MessageType, AgentStatus
from core.ai_client import ai_client

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """
    审稿人Agent
    
    职责：
    - 检查论文逻辑严密性
    - 验证统计方法正确性
    - 评估图表质量和规范性
    - 检查语言表达和语法
    - 提出具体修改建议
    - 评估论文整体质量
    """
    
    def __init__(
        self,
        agent_id: str = "reviewer_agent",
        agent_name: str = "审稿人",
        ai_model: str = "gpt-4o-mini"
    ):
        system_prompt = """你是一位严格的学术期刊审稿人，以高标准审核科研论文。

你的职责：
1. 逻辑审查：检查研究设计、论证逻辑是否严密
2. 方法审查：验证统计方法选择是否合适，计算是否正确
3. 结果审查：检查结果呈现是否客观、完整
4. 图表审查：评估图表质量、规范性
5. 语言审查：检查表达是否清晰、语法是否正确
6. 提出建议：给出具体、可操作的修改建议

审稿原则：
- 严格：以高标准要求
- 公正：客观评价优点和不足
- 建设性：提供有帮助的建议
- 具体：指出具体问题和修改方向
- 全面：从多个维度评估

审稿报告格式：
1. 总体评价（Accept/Minor Revision/Major Revision/Reject）
2. 主要优点（3-5条）
3. 主要问题（按重要性排序）
4. 具体修改建议（逐条列出）
5. 次要问题和建议
"""
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type="reviewer",
            ai_model=ai_model,
            system_prompt=system_prompt
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理审稿任务
        
        Args:
            task: 任务内容，包含：
                - task_name: 任务名称
                - description: 任务描述
                - requirements: 审稿要求（如review_type、focus_areas等）
                - context: 包含论文各部分内容、分析结果等
                
        Returns:
            审稿报告
        """
        task_name = task.get("task_name", "")
        description = task.get("description", "")
        requirements = task.get("requirements", {})
        context = task.get("context", {})
        
        logger.info(f"[{self.agent_name}] 开始审稿任务: {task_name}")
        
        try:
            self.status = AgentStatus.THINKING
            await self._broadcast_status_update()
            
            review_type = requirements.get("review_type", "full")  # full/statistical/writing
            focus_areas = requirements.get("focus_areas", [])
            
            review_report = await self._generate_review_report(
                review_type=review_type,
                focus_areas=focus_areas,
                context=context
            )
            
            self.status = AgentStatus.WORKING
            await self._broadcast_status_update()
            
            logger.info(f"[{self.agent_name}] 审稿完成")
            
            return {
                "status": "success",
                "review_report": review_report,
                "recommendation": review_report.get("recommendation", "Minor Revision")
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] 审稿失败: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_review_report(
        self,
        review_type: str,
        focus_areas: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成审稿报告"""
        
        # 收集论文内容
        paper_content = {
            "abstract": context.get("abstract", ""),
            "introduction": context.get("introduction", ""),
            "methods": context.get("methods", ""),
            "results": context.get("results", ""),
            "discussion": context.get("discussion", ""),
            "conclusion": context.get("conclusion", "")
        }
        
        # 收集分析信息
        research_info = {
            "research_goal": context.get("research_goal", ""),
            "data_info": context.get("data_info", {}),
            "statistical_results": context.get("statistical_results", ""),
            "visualizations": context.get("visualizations", [])
        }
        
        # 构建审稿提示词
        prompt = f"""请对以下论文进行审稿，提供详细的审稿报告。

审稿类型：{review_type}
关注领域：{', '.join(focus_areas) if focus_areas else '全面审查'}

论文内容：
---
Abstract:
{paper_content.get('abstract', '未提供')}

Introduction:
{paper_content.get('introduction', '未提供')}

Methods:
{paper_content.get('methods', '未提供')}

Results:
{paper_content.get('results', '未提供')}

Discussion:
{paper_content.get('discussion', '未提供')}

Conclusion:
{paper_content.get('conclusion', '未提供')}
---

研究信息：
- 研究目标：{research_info['research_goal']}
- 数据规模：{research_info.get('data_info', {}).get('total_rows', 'N/A')}行
- 统计结果：{research_info['statistical_results'][:500] if research_info['statistical_results'] else '无'}...
- 图表数量：{len(research_info.get('visualizations', []))}个

请提供审稿报告，包含以下内容：

1. **总体评价**（Overall Assessment）
   - 推荐决定：Accept / Minor Revision / Major Revision / Reject
   - 一句话总结

2. **主要优点**（Strengths）
   - 列出3-5个优点
   - 具体说明

3. **主要问题**（Major Issues）
   - 按重要性排序
   - 每个问题要具体指出在哪里、是什么问题

4. **具体修改建议**（Specific Recommendations）
   - 逐条列出可操作的修改建议
   - 格式：问题 → 建议如何修改

5. **次要问题**（Minor Issues）
   - 语言、格式等小问题

6. **统计方法评估**（Statistical Methods，如适用）
   - 方法选择是否合适
   - 计算是否正确
   - 结果解读是否准确

请以JSON格式输出，方便后续处理：
{{
  "recommendation": "Minor Revision",
  "overall_assessment": "...",
  "strengths": ["...", "..."],
  "major_issues": ["...", "..."],
  "specific_recommendations": ["...", "..."],
  "minor_issues": ["...", "..."],
  "statistical_assessment": "..."
}}
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.5)
            
            # 尝试解析JSON
            import json
            import re
            
            # 提取JSON（可能包含在```json```代码块中）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            try:
                review_data = json.loads(json_str)
            except json.JSONDecodeError:
                # 如果解析失败，返回纯文本格式
                review_data = {
                    "recommendation": "Minor Revision",
                    "overall_assessment": response,
                    "strengths": [],
                    "major_issues": [],
                    "specific_recommendations": [],
                    "minor_issues": [],
                    "statistical_assessment": ""
                }
            
            return review_data
            
        except Exception as e:
            logger.error(f"生成审稿报告失败: {e}", exc_info=True)
            return {
                "recommendation": "Error",
                "overall_assessment": f"审稿过程出错: {str(e)}",
                "strengths": [],
                "major_issues": [],
                "specific_recommendations": [],
                "minor_issues": [],
                "statistical_assessment": ""
            }

