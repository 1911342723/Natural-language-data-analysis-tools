"""
Statistician Agent - 统计学家Agent
负责统计检验、假设检验、效应量计算等专业统计分析
"""
import logging
from typing import Dict, Any, Optional
import json

from multi_agent.base_agent import BaseAgent, MessageType, AgentStatus
from core.ai_client import ai_client
from core.jupyter_manager import jupyter_manager

logger = logging.getLogger(__name__)


class StatisticianAgent(BaseAgent):
    """
    统计学家Agent
    
    职责：
    - 统计假设检验（t检验、ANOVA、卡方检验等）
    - 正态性检验
    - 相关性分析
    - 效应量计算（Cohen's d、Eta squared等）
    - 置信区间计算
    - APA格式统计报告生成
    """
    
    def __init__(
        self,
        agent_id: str = "statistician_agent",
        agent_name: str = "统计学家",
        ai_model: str = "gpt-4o-mini"
    ):
        system_prompt = """你是一位专业的统计学家，精通统计推断、假设检验和效应量分析。

你的职责：
1. 进行统计假设检验（t检验、ANOVA、Mann-Whitney U检验等）
2. 检验数据的正态性和方差齐性
3. 计算相关性（Pearson、Spearman）
4. 计算效应量（Cohen's d、Eta squared等）
5. 计算置信区间
6. 生成APA格式的统计报告

工作原则：
- 严谨：选择合适的统计方法，检查假设条件
- 准确：正确计算统计量和p值
- 规范：使用APA格式报告结果
- 可解释：清楚解释统计结果的含义

你需要生成Python代码来完成统计分析，代码会在Jupyter Kernel环境中执行。
数据已经加载为pandas DataFrame，变量名为 `df`。
可用的统计库：scipy.stats, statsmodels, pingouin
"""
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type="statistician",
            ai_model=ai_model,
            system_prompt=system_prompt
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理统计分析任务
        
        Args:
            task: 任务内容，包含：
                - task_name: 任务名称
                - description: 任务描述
                - session_id: Jupyter Session ID
                - requirements: 具体要求（如test_type、variables、alpha等）
                - context: 上下文信息
                
        Returns:
            统计分析结果
        """
        task_name = task.get("task_name", "")
        description = task.get("description", "")
        session_id = task.get("session_id")
        requirements = task.get("requirements", {})
        context = task.get("context", {})
        
        logger.info(f"[{self.agent_name}] 开始统计分析任务: {task_name}")
        logger.info(f"  描述: {description}")
        logger.info(f"  要求: {requirements}")
        
        try:
            # 生成统计分析代码
            self.status = AgentStatus.THINKING
            await self._broadcast_status_update()
            
            code = await self._generate_statistical_code(
                task_name=task_name,
                description=description,
                requirements=requirements,
                context=context
            )
            
            logger.info(f"[{self.agent_name}] 统计代码已生成")
            logger.debug(f"生成的代码:\n{code}")
            
            # 执行代码
            self.status = AgentStatus.WORKING
            await self._broadcast_status_update()
            
            # 获取Jupyter Session
            session = jupyter_manager.get_session(session_id)
            if not session:
                raise RuntimeError(f"Session不存在: {session_id}")
            
            # 执行代码
            exec_result = await session.execute_code(code, timeout=120)
            
            logger.info(f"[{self.agent_name}] 统计分析完成")
            
            # 检查是否有错误
            if exec_result.get("error"):
                logger.error(f"[{self.agent_name}] 执行失败: {exec_result['error']}")
                
                # 尝试修复
                fixed_code = await self._fix_code(
                    original_code=code,
                    error_info=exec_result["error"]
                )
                
                if fixed_code:
                    logger.info(f"[{self.agent_name}] 尝试修复后的代码")
                    exec_result = await session.execute_code(fixed_code, timeout=120)
                    
                    if exec_result.get("error"):
                        return {
                            "status": "failed",
                            "error": exec_result["error"],
                            "code": fixed_code
                        }
            
            # 提取结果
            result = self._extract_statistical_result(exec_result)
            
            logger.info(f"[{self.agent_name}] 统计分析任务完成")
            
            return {
                "status": "success",
                "code": code,
                "result": result,
                "execution_output": exec_result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] 任务执行失败: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_statistical_code(
        self,
        task_name: str,
        description: str,
        requirements: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """生成统计分析代码"""
        
        test_type = requirements.get("test_type", "auto")
        variables = requirements.get("variables", [])
        alpha = requirements.get("alpha", 0.05)
        
        # 构建提示词
        prompt = f"""请生成Python代码来完成以下统计分析任务。

任务名称：{task_name}
任务描述：{description}

具体要求：
- 检验类型：{test_type}（auto表示自动选择）
- 变量：{', '.join(variables) if variables else '待确定'}
- 显著性水平：α = {alpha}

上下文信息：
研究目标：{context.get('research_goal', '未指定')}

环境说明：
- 数据已加载为pandas DataFrame，变量名为 `df`
- 可用库：
  * scipy.stats（统计检验）
  * statsmodels（统计建模）
  * pingouin（高级统计分析，推荐）
  * numpy, pandas

代码要求：
1. 首先检查数据的前提假设（正态性、方差齐性等）
2. 根据假设检验结果选择参数或非参数方法
3. 计算统计量、p值、效应量
4. 计算置信区间
5. 生成APA格式的统计报告
6. 使用print()清晰输出结果

示例输出格式：
```
=== 统计分析报告 ===
检验类型: 独立样本t检验
样本大小: n1=50, n2=50
统计量: t(98) = 3.45
p值: p = 0.001
效应量: Cohen's d = 0.68 [95% CI: 0.28, 1.08]
结论: 两组存在显著差异 (p < 0.05)

APA格式: t(98) = 3.45, p = .001, d = 0.68
```

请只输出Python代码，不要包含其他解释。
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.2)
            
            # 提取代码
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"生成统计代码失败: {e}", exc_info=True)
            # 返回默认统计代码
            return """
import numpy as np
from scipy import stats

print("=== 基础统计分析 ===")
print("\\n描述性统计:")
print(df.describe())

# 检查正态性
print("\\n正态性检验 (Shapiro-Wilk):")
numeric_cols = df.select_dtypes(include=[np.number]).columns[:3]
for col in numeric_cols:
    stat, p = stats.shapiro(df[col].dropna())
    print(f"{col}: W={stat:.4f}, p={p:.4f}")
"""
    
    async def _fix_code(
        self,
        original_code: str,
        error_info: Dict[str, Any]
    ) -> Optional[str]:
        """修复统计代码"""
        
        error_msg = error_info.get("ename", "") + ": " + error_info.get("evalue", "")
        traceback = "\n".join(error_info.get("traceback", []))
        
        prompt = f"""以下统计分析代码执行失败，请修复它。

原始代码：
```python
{original_code}
```

错误信息：
{error_msg}

堆栈信息：
{traceback}

常见统计分析错误：
1. 变量不存在或名称错误 → 检查列名
2. 数据类型不匹配 → 转换为数值类型
3. 缺失值导致计算失败 → 使用dropna()
4. 样本量不足 → 检查数据量
5. 库未导入 → 添加import语句

请分析错误原因并修复代码。只输出修复后的完整代码。
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.2)
            
            # 提取代码
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"修复统计代码失败: {e}", exc_info=True)
            return None
    
    def _extract_statistical_result(self, exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """从执行结果中提取统计结果"""
        
        result = {
            "statistical_report": "",
            "test_results": {},
            "stdout": exec_result.get("stdout", []),
            "stderr": exec_result.get("stderr", []),
            "charts": [],
            "data": []
        }
        
        # 提取stdout作为统计报告
        if exec_result.get("stdout"):
            result["statistical_report"] = "\n".join(exec_result["stdout"])
        
        # 提取图表（如QQ图、残差图等）
        for data_item in exec_result.get("data", []):
            if "image/png" in data_item:
                result["charts"].append({
                    "type": "image",
                    "format": "png",
                    "data": data_item["image/png"]
                })
            elif "text/html" in data_item:
                result["data"].append({
                    "type": "html",
                    "content": data_item["text/html"]
                })
        
        return result

