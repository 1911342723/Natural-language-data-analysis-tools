"""
Data Scientist Agent - 数据科学家Agent
负责数据清洗、探索性分析、特征工程等
"""
import logging
from typing import Dict, Any, Optional
import json

from multi_agent.base_agent import BaseAgent, MessageType, AgentStatus
from core.ai_client import ai_client
from core.jupyter_manager import jupyter_manager

logger = logging.getLogger(__name__)


class DataScientistAgent(BaseAgent):
    """
    数据科学家Agent
    
    职责：
    - 数据质量检查（缺失值、异常值）
    - 探索性数据分析（EDA）
    - 描述性统计
    - 数据可视化
    - 特征工程
    """
    
    def __init__(
        self,
        agent_id: str = "data_scientist_agent",
        agent_name: str = "数据科学家",
        ai_model: str = "gpt-4o-mini"
    ):
        system_prompt = """你是一位专业的数据科学家，擅长数据清洗、探索性分析和可视化。

你的职责：
1. 检查数据质量（缺失值、重复值、异常值）
2. 进行探索性数据分析（EDA）
3. 计算描述性统计指标
4. 生成数据可视化图表
5. 进行特征工程

工作原则：
- 严谨：仔细检查数据，不放过任何异常
- 直观：用图表和统计指标清晰展示数据特征
- 高效：编写优化的pandas代码
- 可复现：确保分析过程可重复

你需要生成Python代码来完成任务，代码会在Jupyter Kernel环境中执行。
数据已经加载为pandas DataFrame，变量名为 `df`。
"""
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type="data_scientist",
            ai_model=ai_model,
            system_prompt=system_prompt
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务
        
        Args:
            task: 任务内容，包含：
                - task_name: 任务名称
                - description: 任务描述
                - session_id: Jupyter Session ID
                - data_info: 数据信息
                - requirements: 具体要求
                - context: 上下文信息
                
        Returns:
            任务结果
        """
        task_name = task.get("task_name", "")
        description = task.get("description", "")
        session_id = task.get("session_id")
        requirements = task.get("requirements", {})
        context = task.get("context", {})
        
        logger.info(f"[{self.agent_name}] 开始任务: {task_name}")
        logger.info(f"  描述: {description}")
        logger.info(f"  要求: {requirements}")
        
        try:
            # 生成分析代码
            self.status = AgentStatus.THINKING
            await self._broadcast_status_update()
            
            code = await self._generate_analysis_code(
                task_name=task_name,
                description=description,
                requirements=requirements,
                context=context
            )
            
            logger.info(f"[{self.agent_name}] 代码已生成")
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
            
            logger.info(f"[{self.agent_name}] 代码执行完成")
            
            # 检查是否有错误
            if exec_result.get("error"):
                logger.error(f"[{self.agent_name}] 执行失败: {exec_result['error']}")
                
                # 尝试修复（最多1次，简化版）
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
            result = self._extract_result(exec_result)
            
            logger.info(f"[{self.agent_name}] 任务完成")
            
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
    
    async def _generate_analysis_code(
        self,
        task_name: str,
        description: str,
        requirements: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """生成分析代码"""
        
        # 构建提示词
        prompt = f"""请生成Python代码来完成以下数据分析任务。

任务名称：{task_name}
任务描述：{description}

具体要求：
{json.dumps(requirements, indent=2, ensure_ascii=False)}

上下文信息：
研究目标：{context.get('research_goal', '未指定')}

环境说明：
- 数据已加载为pandas DataFrame，变量名为 `df`
- 可用库：pandas, numpy, matplotlib, seaborn, scipy, statsmodels
- 图表需要通过 plt.show() 显示
- 如果需要返回数据，使用 print() 或直接显示变量

要求：
1. 代码要简洁高效
2. 使用适当的注释
3. 生成的图表要清晰美观
4. 处理潜在的异常情况（如缺失值）

请只输出Python代码，不要包含其他解释。
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.3)
            
            # 提取代码
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                # 如果没有代码块，假设整个响应都是代码
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"生成代码失败: {e}", exc_info=True)
            # 返回一个简单的默认代码
            return """
# 数据基本信息
print("数据形状:", df.shape)
print("\\n字段信息:")
print(df.info())
print("\\n描述性统计:")
print(df.describe())
"""
    
    async def _fix_code(
        self,
        original_code: str,
        error_info: Dict[str, Any]
    ) -> Optional[str]:
        """修复代码"""
        
        error_msg = error_info.get("ename", "") + ": " + error_info.get("evalue", "")
        traceback = "\n".join(error_info.get("traceback", []))
        
        prompt = f"""以下代码执行失败，请修复它。

原始代码：
```python
{original_code}
```

错误信息：
{error_msg}

堆栈信息：
{traceback}

请分析错误原因并修复代码。只输出修复后的完整代码，不要包含其他解释。
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.3)
            
            # 提取代码
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"修复代码失败: {e}", exc_info=True)
            return None
    
    def _extract_result(self, exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """从执行结果中提取有用信息"""
        
        result = {
            "stdout": exec_result.get("stdout", []),
            "stderr": exec_result.get("stderr", []),
            "charts": [],
            "data": []
        }
        
        # 提取图表（base64编码的PNG）
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
            elif "text/plain" in data_item:
                result["data"].append({
                    "type": "text",
                    "content": data_item["text/plain"]
                })
        
        return result

