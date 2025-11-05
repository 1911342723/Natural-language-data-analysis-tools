"""
智能自主 Agent：具备规划、反思、迭代优化能力
类似人类数据分析师的思维流程
"""
import asyncio
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ai_client import ai_client
from .jupyter_manager import jupyter_manager

logger = logging.getLogger(__name__)


class AgentStep:
    """Agent 执行步骤（动态生成）"""
    
    def __init__(
        self,
        step_id: int,
        title: str,
        description: str = "",
        step_type: str = "analysis",  # planning | exploration | analysis | reflection | summary
        status: str = "waiting"
    ):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.step_type = step_type
        self.status = status  # waiting | running | success | failed
        self.code: Optional[str] = None
        self.output: Optional[str] = None
        self.error: Optional[Dict] = None
        self.result: Optional[Dict] = None
        self.reasoning: Optional[str] = None  # AI的思考过程
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "step_type": self.step_type,
            "status": self.status,
            "code": self.code,
            "output": self.output,
            "error": self.error,
            "result": self.result,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
        }


class SmartAnalysisAgent:
    """智能数据分析 Agent - 具备自主决策能力"""
    
    def __init__(
        self,
        session_id: str,
        user_request: str,
        selected_columns: List[str],
        data_schema: Dict,
        tables_info: Optional[List[Dict]] = None,
        conversation_history: List[Dict[str, str]] = []
    ):
        self.session_id = session_id
        self.user_request = user_request
        self.selected_columns = selected_columns
        self.conversation_history = conversation_history or []
        self.data_schema = data_schema
        self.tables_info = tables_info
        
        self.steps: List[AgentStep] = []
        self.step_counter = 0
        self.status = "running"  # running | completed | failed
        self.final_result: Optional[Dict] = None
        self.summary: Optional[str] = None  # AI 生成的总结
        self.error_message: Optional[str] = None
        
        # 执行历史（用于反思和决策）
        self.execution_history: List[Dict] = []
        self.generated_visualizations: List[str] = []  # 已生成的可视化类型
        
        self.max_iterations = 5  # 最大迭代次数（防止无限循环）
        self.current_iteration = 0
        
        self._cancelled = False
    
    async def run(self) -> Dict[str, Any]:
        """运行智能 Agent"""
        logger.info(f"🧠 智能 Agent 开始运行 (session: {self.session_id})")
        logger.info(f"📝 用户需求: {self.user_request}")
        print(f"\n{'='*60}")
        print(f"🧠 [智能模式] 开始运行")
        print(f"📝 用户需求: {self.user_request}")
        print(f"{'='*60}\n")
        
        try:
            # ====== 第1步：规划分析策略 ======
            plan_step = await self._create_step(
                title="🎯 规划分析策略",
                description="分析用户需求，制定数据分析计划",
                step_type="planning"
            )
            await self._plan_analysis(plan_step)
            
            if plan_step.status == "failed":
                self.status = "failed"
                self.error_message = "规划失败"
                return self._build_response()
            
            # ====== 第2步：探索数据（如果需要）======
            if self._need_data_exploration(plan_step):
                explore_step = await self._create_step(
                    title="🔍 探索数据",
                    description="查看数据结构、统计信息、数据分布",
                    step_type="exploration"
                )
                await self._explore_data(explore_step)
            
            # ====== 主循环：迭代分析直到满意 ======
            is_satisfied = False
            while not is_satisfied and self.current_iteration < self.max_iterations:
                self.current_iteration += 1
                logger.info(f"🔄 开始第 {self.current_iteration} 轮分析")
                
                # 检查是否取消
                if self._cancelled:
                    raise asyncio.CancelledError("Agent 任务已被取消")
                
                # ====== 决定下一步分析 ======
                decision_step = await self._create_step(
                    title=f"💡 决策（第{self.current_iteration}轮）",
                    description="根据当前结果决定下一步分析方向",
                    step_type="reflection"
                )
                next_action = await self._decide_next_action(decision_step)
                
                if next_action["action"] == "stop":
                    # AI认为已经足够回答用户问题
                    is_satisfied = True
                    logger.info("✅ AI判断：分析结果已充分")
                    break
                
                # ====== 生成并执行新的分析代码 ======
                analysis_step = await self._create_step(
                    title=next_action.get("title", f"📊 分析（第{self.current_iteration}轮）"),
                    description=next_action.get("description", "执行数据分析"),
                    step_type="analysis"
                )
                
                await self._generate_and_execute(analysis_step, next_action)
                
                if analysis_step.status == "failed":
                    # 尝试修复
                    fix_success = await self._try_fix_code(analysis_step)
                    if not fix_success:
                        logger.warning(f"⚠️ 第{self.current_iteration}轮分析失败，继续下一轮")
                        continue
                
                # 记录到执行历史
                self.execution_history.append({
                    "iteration": self.current_iteration,
                    "action": next_action,
                    "result": analysis_step.result,
                    "visualization_type": next_action.get("visualization_type")
                })
                
                # 记录已生成的可视化类型
                if next_action.get("visualization_type"):
                    self.generated_visualizations.append(next_action["visualization_type"])
            
            # ====== 最后一步：生成总结 ======
            summary_step = await self._create_step(
                title="📋 生成总结",
                description="汇总所有分析结果，生成综合报告",
                step_type="summary"
            )
            await self._generate_comprehensive_summary(summary_step)
            
            # ====== 提取最终结果 ======
            self._extract_final_result()
            
            self.status = "completed"
            logger.info(f"🎉 智能 Agent 执行完成 (session: {self.session_id})")
            return self._build_response()
            
        except asyncio.CancelledError:
            logger.info(f"Agent 任务已取消 (session: {self.session_id})")
            self.status = "failed"
            self.error_message = "任务已取消"
            return self._build_response()
        except Exception as e:
            logger.exception(f"Agent 执行异常: {e}")
            self.status = "failed"
            self.error_message = str(e)
            return self._build_response()
    
    async def _create_step(self, title: str, description: str, step_type: str) -> AgentStep:
        """创建并添加新步骤"""
        self.step_counter += 1
        step = AgentStep(
            step_id=self.step_counter,
            title=title,
            description=description,
            step_type=step_type,
            status="running"
        )
        self.steps.append(step)
        return step
    
    async def _plan_analysis(self, step: AgentStep):
        """规划分析策略"""
        logger.info("🎯 开始规划分析策略")
        
        # 构建规划提示词
        prompt = self._build_planning_prompt()
        
        try:
            step.output = ""
            # 将 prompt 转换为消息格式
            messages = [{"role": "user", "content": prompt}]
            for chunk in ai_client.chat_stream(messages):
                step.output += chunk
                await asyncio.sleep(0.01)  # 让出控制权，使SSE可以推送
            
            # 解析规划结果
            plan = self._parse_planning_output(step.output)
            step.reasoning = plan.get("reasoning", "")
            step.status = "success"
            logger.info(f"✅ 规划完成: {plan.get('strategy', '未知')}")
            
        except Exception as e:
            logger.error(f"规划失败: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
    
    def _need_data_exploration(self, plan_step: AgentStep) -> bool:
        """判断是否需要数据探索"""
        # 如果用户需求很模糊，或者规划建议探索数据
        vague_keywords = ["合适", "适当", "最好", "帮我", "分析一下", "看看", "探索"]
        user_request_lower = self.user_request.lower()
        
        for keyword in vague_keywords:
            if keyword in user_request_lower:
                return True
        
        # 检查规划输出中是否提到需要探索
        if plan_step.output and ("探索" in plan_step.output or "了解数据" in plan_step.output):
            return True
        
        return False
    
    async def _explore_data(self, step: AgentStep):
        """探索数据"""
        logger.info("🔍 开始探索数据")
        
        # 生成数据探索代码
        explore_code = self._generate_exploration_code()
        step.code = explore_code
        
        try:
            # 获取 session 并执行探索代码
            session = jupyter_manager.get_session(self.session_id)
            if not session:
                raise Exception(f"Session 不存在: {self.session_id}")
            
            result = await session.execute_code(explore_code, timeout=60)
            
            # 组合输出
            output_lines = []
            if result.get('stdout'):
                output_lines.extend(result['stdout'])
            if result.get('data'):
                output_lines.append(f"\n收集到 {len(result['data'])} 个数据对象")
            
            step.output = "\n".join(output_lines)
            step.result = result
            
            # 判断状态
            if result.get('error'):
                has_output = bool(result.get('stdout') or result.get('data'))
                step.status = "success" if has_output else "failed"
                if not has_output:
                    step.error = result['error']
                    logger.error(f"❌ 数据探索失败: {result['error']}")
            else:
                step.status = "success"
                logger.info("✅ 数据探索完成")
                
        except Exception as e:
            logger.error(f"数据探索异常: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
    
    def _generate_exploration_code(self) -> str:
        """生成数据探索代码"""
        is_multi = self.tables_info is not None and len(self.tables_info) > 0
        
        if is_multi:
            # 多表模式
            code_lines = [
                "# 数据探索",
                "import pandas as pd",
                "import numpy as np",
                "",
                "exploration_results = {}"
            ]
            
            for table in self.tables_info:
                alias = table['alias']
                code_lines.extend([
                    f"",
                    f"# === {alias} ===",
                    f"exploration_results['{alias}'] = {{",
                    f"    'shape': {alias}.shape,",
                    f"    'columns': {alias}.columns.tolist(),",
                    f"    'dtypes': {alias}.dtypes.to_dict(),",
                    f"    'missing': {alias}.isnull().sum().to_dict(),",
                    f"    'stats': {alias}.describe().to_dict()",
                    f"}}"
                ])
            
            code_lines.append("exploration_results")
        else:
            # 单表模式
            code_lines = [
                "# 数据探索",
                "import pandas as pd",
                "import numpy as np",
                "",
                "exploration_results = {",
                "    'shape': df.shape,",
                "    'columns': df.columns.tolist(),",
                "    'dtypes': df.dtypes.to_dict(),",
                "    'missing': df.isnull().sum().to_dict(),",
                "    'stats': df.describe().to_dict()",
                "}",
                "exploration_results"
            ]
        
        return "\n".join(code_lines)
    
    async def _decide_next_action(self, step: AgentStep) -> Dict[str, Any]:
        """决定下一步行动"""
        logger.info("💡 决定下一步行动")
        
        prompt = self._build_decision_prompt()
        
        try:
            step.output = ""
            messages = [{"role": "user", "content": prompt}]
            for chunk in ai_client.chat_stream(messages):
                step.output += chunk
                await asyncio.sleep(0.01)
            
            # 解析决策结果
            decision = self._parse_decision_output(step.output)
            step.reasoning = decision.get("reasoning", "")
            step.status = "success"
            
            logger.info(f"✅ 决策完成: {decision.get('action', 'unknown')}")
            return decision
            
        except Exception as e:
            logger.error(f"决策失败: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
            # 返回默认决策：停止
            return {"action": "stop", "reasoning": "决策失败，停止分析"}
    
    async def _generate_and_execute(self, step: AgentStep, action: Dict):
        """生成并执行分析代码"""
        logger.info(f"📊 生成并执行分析代码: {action.get('visualization_type', 'unknown')}")
        
        # 生成代码
        code_prompt = self._build_code_generation_prompt(action)
        
        try:
            # 流式生成代码
            step.output = ""
            messages = [{"role": "user", "content": code_prompt}]
            for chunk in ai_client.chat_stream(messages):
                step.output += chunk
                await asyncio.sleep(0.01)
            
            # 提取代码
            code = self._extract_code_from_output(step.output)
            step.code = code
            
            # 获取 session 并执行代码
            session = jupyter_manager.get_session(self.session_id)
            if not session:
                raise Exception(f"Session 不存在: {self.session_id}")
            
            result = await session.execute_code(code, timeout=60)
            
            print(f"📊 [智能模式] 代码执行完成:")
            print(f"  - stdout: {len(result.get('stdout', []))} 项")
            print(f"  - data: {len(result.get('data', []))} 项") 
            print(f"  - error: {result.get('error')}")
            
            step.result = result
            
            # 格式化输出（像经典Agent一样）
            output_lines = []
            
            if result.get('error'):
                # 如果有错误但有输出，算部分成功
                has_output = bool(result.get('stdout') or result.get('data'))
                step.status = "success" if has_output else "failed"
                
                if result.get('stdout'):
                    output_lines.append("=== 标准输出 ===")
                    output_lines.extend(result['stdout'])
                if result.get('stderr'):
                    output_lines.append("\n=== 错误输出 ===")
                    output_lines.extend(result['stderr'])
                    
                if not has_output:
                    step.error = result['error']
                    logger.error(f"❌ 执行失败: {result.get('error')}")
                else:
                    output_lines.append(f"\n⚠️ 注意：代码执行过程中遇到错误: {result['error'].get('evalue', '')}")
                    logger.info("✅ 执行成功（有部分输出）")
            else:
                step.status = "success"
                # stdout
                if result.get('stdout'):
                    output_lines.append("=== 标准输出 ===")
                    output_lines.extend(result['stdout'])
                
                # display 数据
                if result.get('data'):
                    output_lines.append("\n=== 可视化输出 ===")
                    for idx, data_item in enumerate(result['data']):
                        data_content = data_item.get('data', data_item)
                        if 'text/plain' in data_content:
                            output_lines.append(f"\n[输出 {idx + 1}]")
                            output_lines.append(data_content['text/plain'])
                        if 'text/html' in data_content:
                            output_lines.append(f"\n[HTML 表格 {idx + 1}]")
                            output_lines.append("(HTML 表格已生成)")
                        if 'image/png' in data_content:
                            output_lines.append(f"\n[图表 {idx + 1}]")
                            output_lines.append("(图表已生成)")
                
                logger.info("✅ 执行成功")
            
            # 更新输出为格式化的执行结果
            step.output = '\n'.join(output_lines) if output_lines else "✅ 代码执行成功（无输出）"
                
        except Exception as e:
            logger.error(f"生成或执行异常: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
    
    async def _try_fix_code(self, step: AgentStep, max_retries: int = 2) -> bool:
        """尝试修复代码"""
        for retry in range(max_retries):
            logger.info(f"🔧 尝试修复代码 (第{retry + 1}次)")
            
            fix_step = await self._create_step(
                title=f"🔧 修复代码（第{retry + 1}次）",
                description="分析错误并修复代码",
                step_type="analysis"
            )
            
            # 生成修复代码
            fix_prompt = self._build_fix_prompt(step.code, step.error)
            
            try:
                fix_step.output = ""
                messages = [{"role": "user", "content": fix_prompt}]
                for chunk in ai_client.chat_stream(messages):
                    fix_step.output += chunk
                    await asyncio.sleep(0.01)
                
                # 提取修复后的代码
                fixed_code = self._extract_code_from_output(fix_step.output)
                fix_step.code = fixed_code
                
                # 获取 session 并执行修复后的代码
                session = jupyter_manager.get_session(self.session_id)
                if not session:
                    raise Exception(f"Session 不存在: {self.session_id}")
                
                result = await session.execute_code(fixed_code, timeout=60)
                fix_step.result = result
                
                # 格式化修复步骤的输出
                output_lines = []
                if result.get('stdout'):
                    output_lines.append("=== 标准输出 ===")
                    output_lines.extend(result['stdout'])
                if result.get('data'):
                    output_lines.append("\n=== 可视化输出 ===")
                    for idx, data_item in enumerate(result['data']):
                        data_content = data_item.get('data', data_item)
                        if 'image/png' in data_content:
                            output_lines.append(f"\n[图表 {idx + 1}]")
                            output_lines.append("(图表已生成)")
                
                # 判断修复是否成功
                if result.get('error'):
                    has_output = bool(result.get('stdout') or result.get('data'))
                    if has_output:
                        fix_step.status = "success"
                        fix_step.output = '\n'.join(output_lines) if output_lines else "✅ 代码执行成功（无输出）"
                        logger.info("✅ 修复成功（有部分输出）")
                        # 更新原步骤
                        step.code = fixed_code
                        step.result = result
                        step.output = fix_step.output
                        step.status = "success"
                        return True
                    else:
                        fix_step.status = "failed"
                        fix_step.error = result['error']
                        logger.error(f"❌ 修复后仍然失败")
                else:
                    fix_step.status = "success"
                    fix_step.output = '\n'.join(output_lines) if output_lines else "✅ 代码执行成功（无输出）"
                    logger.info("✅ 修复成功")
                    # 更新原步骤
                    step.code = fixed_code
                    step.result = result
                    step.output = fix_step.output
                    step.status = "success"
                    return True
                    
            except Exception as e:
                logger.error(f"修复异常: {e}")
                fix_step.status = "failed"
                fix_step.error = {"message": str(e)}
        
        return False
    
    async def _generate_comprehensive_summary(self, step: AgentStep):
        """生成综合总结"""
        logger.info("📋 生成综合总结")
        
        prompt = self._build_summary_prompt()
        
        try:
            step.output = ""
            messages = [{"role": "user", "content": prompt}]
            for chunk in ai_client.chat_stream(messages):
                step.output += chunk
                await asyncio.sleep(0.01)
            
            # 保存总结到实例变量
            self.summary = step.output
            
            step.status = "success"
            logger.info("✅ 总结生成完成")
            
        except Exception as e:
            logger.error(f"总结生成失败: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
    
    def _extract_final_result(self):
        """提取所有分析步骤的最终结果（类似经典Agent）"""
        logger.info("📦 开始提取最终结果")
        print(f"📦 [智能模式] 开始提取最终结果，共 {len(self.steps)} 个步骤")
        
        result = {
            'data': [],
            'charts': [],
            'text': []
        }
        
        # 遍历所有步骤，收集结果
        for step in self.steps:
            print(f"📦 [智能模式] 检查步骤: {step.title}, type={step.step_type}, has_result={step.result is not None}")
            # 只处理分析步骤和探索步骤（有实际执行结果的）
            if step.step_type in ['analysis', 'exploration'] and step.result:
                exec_result = step.result
                print(f"📦 [智能模式] 步骤 '{step.title}' 有结果:")
                print(f"  - stdout: {len(exec_result.get('stdout', []))} 项")
                print(f"  - data: {len(exec_result.get('data', []))} 项")
                print(f"  - error: {exec_result.get('error')}")
                
                # 收集 stdout 文本输出
                if exec_result.get('stdout'):
                    full_text = ''.join(exec_result['stdout'])
                    if full_text.strip():
                        result['text'].append(full_text)
                        logger.info(f"✅ 从步骤 '{step.title}' 提取到 stdout: {len(full_text)} 字符")
                        print(f"✅ [智能模式] 提取到 stdout: {len(full_text)} 字符")
                
                # 收集图表和表格
                if exec_result.get('data'):
                    print(f"📦 [智能模式] 开始处理 {len(exec_result['data'])} 个 data 项")
                    for idx, data_item in enumerate(exec_result['data']):
                        data_content = data_item.get('data', data_item)
                        print(f"  📦 data[{idx}] keys: {list(data_content.keys()) if isinstance(data_content, dict) else type(data_content)}")
                        
                        # 处理 HTML 表格
                        if 'text/html' in data_content:
                            html_content = data_content['text/html']
                            result['data'].append({
                                'type': 'html',
                                'content': html_content
                            })
                            logger.info(f"✅ 从步骤 '{step.title}' 提取到 HTML 表格")
                            print(f"✅ [智能模式] 提取到 HTML 表格")
                        
                        # 处理图片
                        if 'image/png' in data_content:
                            result['charts'].append({
                                'type': 'image',
                                'format': 'png',
                                'data': data_content['image/png']
                            })
                            logger.info(f"✅ 从步骤 '{step.title}' 提取到图表")
                            print(f"✅ [智能模式] 提取到图表")
        
        # 清理空数组
        if not result['data']:
            del result['data']
        if not result['charts']:
            del result['charts']
        if not result['text']:
            del result['text']
        
        # 如果result完全为空，添加一个提示
        if not result:
            result['text'] = ["⚠️ 未捕获到输出，请检查代码是否有 print 语句或图表生成"]
            logger.warning("⚠️ result 为空，添加提示信息")
            print(f"⚠️ [智能模式] result 为空，添加提示信息")
        
        print(f"📦 [智能模式] 最终结果: charts={len(result.get('charts', []))}, data={len(result.get('data', []))}, text={len(result.get('text', []))}")
        logger.info(f"📦 最终结果提取完成: charts={len(result.get('charts', []))}, data={len(result.get('data', []))}, text={len(result.get('text', []))}")
        
        self.final_result = result
    
    def _build_planning_prompt(self) -> str:
        """构建规划提示词"""
        from .prompts import build_conversation_context
        
        conversation_context = build_conversation_context(self.conversation_history)
        
        return f"""你是一位资深数据分析师。用户提出了以下需求：

【对话历史】
{conversation_context}

【当前需求】
"{self.user_request}"

可用的数据信息：
- 字段: {', '.join(self.selected_columns)}
- 数据schema: {json.dumps(self.data_schema, ensure_ascii=False)}

请分析这个需求，制定一个分析计划。考虑：
1. 用户需求是否清晰？是否需要先探索数据？
2. 需要什么类型的分析？（统计分析、可视化、相关性分析等）
3. 可能需要哪些可视化图表？
4. 分析的优先级和顺序？

请以JSON格式返回你的规划：
{{
    "reasoning": "你的分析思路",
    "strategy": "分析策略描述",
    "need_exploration": true/false,
    "suggested_analyses": ["分析1", "分析2", ...]
}}"""
    
    def _build_decision_prompt(self) -> str:
        """构建决策提示词"""
        history_desc = self._format_execution_history()
        
        return f"""你是一位资深数据分析师。

**用户需求**: {self.user_request}

**已完成的分析**:
{history_desc}

**已生成的可视化**: {', '.join(self.generated_visualizations) if self.generated_visualizations else '无'}

**当前是第 {self.current_iteration} 轮分析**

请判断：
1. 当前的分析结果是否已经充分回答了用户的问题？
2. 如果不够，还需要什么类型的分析或可视化？
3. 是否需要从不同角度补充分析？

请以JSON格式返回决策：
{{
    "action": "continue" 或 "stop",
    "reasoning": "你的判断理由",
    "visualization_type": "如果继续，建议的可视化类型（bar/line/scatter/pie/heatmap/box等）",
    "title": "如果继续，这一步的标题",
    "description": "如果继续，这一步的描述",
    "analysis_focus": "如果继续，这一步的分析重点"
}}

注意：
- 如果已经充分回答用户问题，请返回 "action": "stop"
- 避免重复已经生成过的可视化类型
- 每种图表应该从不同角度回答用户问题
"""
    
    def _build_code_generation_prompt(self, action: Dict) -> str:
        """构建代码生成提示词"""
        # TODO: 实现详细的代码生成提示词
        return f"""你是Python数据分析专家。

**用户需求**: {self.user_request}

**当前任务**: {action.get('title', '数据分析')}
**分析重点**: {action.get('analysis_focus', '未指定')}
**可视化类型**: {action.get('visualization_type', 'auto')}

**重要提示：数据已经加载好！**
- **DataFrame名称：df（已经加载在环境中，包含所有用户上传的数据）**
- **可用字段**: {', '.join(self.selected_columns)}
- **请直接使用 df，不要创建模拟数据！**
- **注意：数据可能包含空值（NaN），请先清理数据（如 dropna()、fillna()）**

请生成Python代码完成这个分析任务。

**关键要求**：
1. **直接使用已有的 df DataFrame，不要创建新数据或模拟数据**
2. **必须生成图表！使用 matplotlib 或 seaborn**
3. **必须使用 IPython.display.Image 显示图表**（不要用 plt.show() 或 plt.gcf()）
4. **可以使用 print() 输出文字分析结果**
5. **图表必须通过 display(Image(buffer)) 方式显示**

示例模式：
```python
import matplotlib.pyplot as plt
import seaborn as sns
import io
from IPython.display import Image, display

# 数据处理
data = df.groupby('字段').mean()

# 创建图表
plt.figure(figsize=(12, 6))
sns.barplot(data=data, ...)
plt.title('标题')
plt.tight_layout()

# ✅ 正确方式：保存到 buffer 并使用 display()
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
buf.seek(0)
plt.close()
display(Image(buf.getvalue()))

# 输出文字分析
print("分析结果...")
```

其他要求：
- 使用中文标签和标题（支持中文字体）
- 代码清晰，添加注释
- 可以在中间用 print() 输出统计信息，但最后一行不要是 print

请用以下格式返回：
```python
# 你的代码
```
"""
    
    def _build_fix_prompt(self, code: str, error: Dict) -> str:
        """构建修复提示词"""
        return f"""代码执行失败，请帮助修复。

**原始代码**:
```python
{code}
```

**错误信息**:
{json.dumps(error, ensure_ascii=False)}

请分析错误原因并修复代码。

**修复要求**：
1. 直接使用已有的 df DataFrame，不要创建模拟数据
2. 如果是图表代码，必须使用 `display(Image(buffer))` 显示图表
3. 不要使用 `plt.show()` 或 `plt.gcf()`
4. 图表保存示例：
```python
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
buf.seek(0)
plt.close()
display(Image(buf.getvalue()))
```

直接返回修复后的完整代码，用```python```包裹。
"""
    
    def _build_summary_prompt(self) -> str:
        """构建总结提示词"""
        # 收集所有步骤的实际输出
        analysis_outputs = []
        for record in self.execution_history:
            iteration = record.get("iteration")
            action = record.get("action", {})
            result = record.get("result", {})
            
            # 提取文本输出
            if result and result.get('stdout'):
                text = "\n".join(result['stdout'])
                analysis_outputs.append(f"### 分析轮次 {iteration}: {action.get('title', '未知')}\n{text[:1000]}")
        
        outputs_text = "\n\n".join(analysis_outputs) if analysis_outputs else "无实际输出"
        
        return f"""你是一位专业的数据分析师。请基于实际的分析结果生成一份综合总结报告。

**用户需求**: {self.user_request}

**实际分析输出**:
{outputs_text[:5000]}

**生成的可视化**: {len(self.generated_visualizations)} 个图表
类型: {', '.join(self.generated_visualizations) if self.generated_visualizations else '无'}

【总结要求】

请**严格基于上述实际分析输出**，生成简洁专业的报告：

## 1. 📊 数据概况
- 数据规模和关键字段
- 数据质量情况

## 2. 🔍 关键发现
- 3-5个最重要的数据发现
- 用具体数字支撑

## 3. 💡 深度洞察
- 数据背后的含义
- 值得关注的模式或异常

## 4. 📋 建议与行动
- 2-3条实用建议
- 优先级说明

【重要原则】
✅ 必须基于实际数据，不要编造
✅ 使用清晰的数字和百分比
✅ 结构化呈现，Markdown格式
❌ 不要偏离实际数据内容
❌ 不要使用无关术语（如"用户活跃度"，除非数据真的是这类）

请开始生成报告：
"""
    
    def _format_execution_history(self) -> str:
        """格式化执行历史"""
        if not self.execution_history:
            return "无"
        
        lines = []
        for i, record in enumerate(self.execution_history, 1):
            action = record.get("action", {})
            lines.append(f"{i}. {action.get('title', '分析')} - {action.get('visualization_type', 'unknown')}")
        
        return "\n".join(lines)
    
    def _parse_planning_output(self, output: str) -> Dict:
        """解析规划输出"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"reasoning": output, "strategy": "未知"}
    
    def _parse_decision_output(self, output: str) -> Dict:
        """解析决策输出"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 默认决策：停止
        return {"action": "stop", "reasoning": "解析失败"}
    
    def _extract_code_from_output(self, output: str) -> str:
        """从输出中提取代码"""
        # 提取 ```python ... ``` 代码块
        pattern = r'```python\s*(.*?)\s*```'
        match = re.search(pattern, output, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 如果没有代码块，返回整个输出
        return output.strip()
    
    def _build_response(self) -> Dict[str, Any]:
        """构建响应（匹配经典Agent的返回格式）"""
        return {
            "status": self.status,
            "data": {
                "steps": [step.to_dict() for step in self.steps],
                "result": self.final_result,
                "summary": self.summary,  # 总结放在外层
                "error": self.error_message,
                "iterations": self.current_iteration,
                "generated_visualizations": self.generated_visualizations
            }
        }
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态（用于SSE推送）"""
        return {
            "status": self.status,
            "data": {
                "steps": [step.to_dict() for step in self.steps],
                "result": self.final_result,
                "summary": self.summary,  # 总结放在外层
                "error": self.error_message,
                "current_iteration": self.current_iteration
            }
        }
    
    def cancel(self):
        """取消执行"""
        self._cancelled = True
        logger.info(f"Agent 任务已标记为取消 (session: {self.session_id})")

