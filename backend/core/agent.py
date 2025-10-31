"""
Agent 核心逻辑：代码生成、执行、修复
"""
import asyncio
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ai_client import ai_client
from .jupyter_manager import jupyter_manager
from .prompts import (
    build_initial_prompt,
    build_fix_prompt,
    build_summary_prompt
)

logger = logging.getLogger(__name__)


class AgentStep:
    """Agent 执行步骤"""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        status: str = "waiting"
    ):
        self.title = title
        self.description = description
        self.status = status  # waiting | running | success | failed
        self.code: Optional[str] = None
        self.output: Optional[str] = None
        self.error: Optional[Dict] = None
        self.result: Optional[Dict] = None
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "code": self.code,
            "output": self.output,
            "error": self.error,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
        }


class AnalysisAgent:
    """数据分析 Agent"""
    
    def __init__(
        self,
        session_id: str,
        user_request: str,
        selected_columns: List[str],
        data_schema: Dict
    ):
        self.session_id = session_id
        self.user_request = user_request
        self.selected_columns = selected_columns
        self.data_schema = data_schema
        
        self.steps: List[AgentStep] = []
        self.status = "running"  # running | completed | failed
        self.final_result: Optional[Dict] = None
        self.error_message: Optional[str] = None
        
        self.max_retries = 3  # 最大重试次数
        self.current_retry = 0
        
        self._cancelled = False  # 取消标志
    
    async def run(self) -> Dict[str, Any]:
        """运行 Agent"""
        logger.info(f"Agent 开始运行 (session: {self.session_id})")
        logger.info(f"用户需求: {self.user_request}")
        logger.info(f"选择字段: {self.selected_columns}")
        
        try:
            # 检查是否已取消
            if self._cancelled:
                raise asyncio.CancelledError("Agent 任务已被取消")
            
            # 步骤1：生成代码
            step1 = await self._generate_code()
            self.steps.append(step1)
            
            if step1.status == "failed":
                self.status = "failed"
                self.error_message = "代码生成失败"
                return self._build_response()
            
            # 循环尝试执行和修复
            while self.current_retry < self.max_retries:
                # 检查是否已取消
                if self._cancelled:
                    raise asyncio.CancelledError("Agent 任务已被取消")
                
                # 步骤2：执行代码
                step2 = await self._execute_code(step1.code)
                self.steps.append(step2)
                
                if step2.status == "success":
                    # 执行成功！
                    # 步骤3：提取结果
                    step3 = await self._extract_result(step2.output, step2.result)
                    self.steps.append(step3)
                    
                    if step3.status == "success":
                        # 步骤4：生成总结
                        step4 = await self._generate_summary()
                        self.steps.append(step4)
                        
                        self.status = "completed"
                        logger.info(f"Agent 执行成功 (session: {self.session_id})")
                        return self._build_response()
                
                # 执行失败，尝试修复
                self.current_retry += 1
                if self.current_retry >= self.max_retries:
                    self.status = "failed"
                    self.error_message = f"达到最大重试次数({self.max_retries})"
                    return self._build_response()
                
                # 步骤3：分析错误并修复
                step3 = await self._fix_code(step1.code, step2.error, step2.output)
                self.steps.append(step3)
                
                if step3.status == "failed":
                    self.status = "failed"
                    self.error_message = "代码修复失败"
                    return self._build_response()
                
                # 使用修复后的代码
                step1.code = step3.code
        
        except Exception as e:
            logger.error(f"Agent 执行异常: {e}", exc_info=True)
            self.status = "failed"
            self.error_message = str(e)
        
        return self._build_response()
    
    async def _generate_code(self) -> AgentStep:
        """步骤1：生成代码"""
        step = AgentStep(
            title="生成代码",
            description="根据用户需求生成 Python 分析代码",
            status="running"
        )
        
        try:
            logger.info("正在生成代码...")
            
            # 构建 prompt
            # 检查是否是多表格模式
            is_multi = self.data_schema.get('is_multi', False)
            if is_multi:
                # 多表格模式：传递 tables_info
                prompt = build_initial_prompt(
                    user_request=self.user_request,
                    selected_columns=[],  # 多表格模式不需要选择字段
                    data_schema={},
                    tables_info=self.data_schema.get('tables', [])
                )
            else:
                # 单表格模式：原有逻辑
                prompt = build_initial_prompt(
                    user_request=self.user_request,
                    selected_columns=self.selected_columns,
                    data_schema=self.data_schema
                )
            
            # 调用 AI（流式）
            messages = [
                {"role": "system", "content": "你是一个专业的Python数据分析代码生成助手。"},
                {"role": "user", "content": prompt}
            ]
            
            # 使用流式接收 AI 响应
            response_chunks = []
            step.output = "🔄 AI 正在思考..."
            
            print(f"\n🤖 [AI 流式生成开始]")
            chunk_count = 0
            last_update_length = 0
            
            for chunk in ai_client.chat_stream(messages, temperature=0.1):
                # 检查是否已取消
                if self._cancelled:
                    logger.info("⚠️ AI 代码生成被用户中断")
                    raise asyncio.CancelledError("AI 代码生成已被取消")
                
                response_chunks.append(chunk)
                chunk_count += 1
                current_response = ''.join(response_chunks)
                
                # 每收到 2 个 token 或内容增加超过 20 个字符就更新一次
                if chunk_count % 2 == 0 or len(current_response) - last_update_length > 20:
                    # 显示完整的实时内容（带省略）
                    if len(current_response) > 500:
                        preview = current_response[:500] + "\n\n... (继续生成中，已生成 " + str(len(current_response)) + " 字符)"
                    else:
                        preview = current_response
                    step.output = f"🔄 AI 正在生成代码...\n\n{preview}"
                    last_update_length = len(current_response)
                    
                    # 主动让出控制权，让 SSE 轮询器有机会检测到变化
                    await asyncio.sleep(0.05)  # 50ms 的暂停
            
            response = ''.join(response_chunks)
            print(f"\n🤖 [AI 响应完成] 总长度: {len(response)} 字符")
            print(f"📄 [响应前500字符] {response[:500]}...")
            
            # 提取代码（去掉markdown格式）
            code = self._extract_code_from_response(response)
            
            print(f"\n📝 [提取的代码]\n{code}\n")
            
            if not code:
                raise Exception("无法从 AI 响应中提取代码")
            
            step.code = code
            step.status = "success"
            step.output = "✅ 代码生成成功"
            
            logger.info("代码生成成功")
        
        except Exception as e:
            print(f"\n❌ [代码生成异常] {type(e).__name__}: {e}")
            import traceback
            print(traceback.format_exc())
            logger.error(f"代码生成失败: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
        
        return step
    
    async def _execute_code(self, code: str) -> AgentStep:
        """步骤2：执行代码"""
        step = AgentStep(
            title="执行代码",
            description="在 Jupyter Kernel 中执行生成的代码",
            status="running"
        )
        
        try:
            print(f"\n🔍 [Agent] 开始执行分析代码, session_id={self.session_id[:8]}")
            
            # 获取 session
            session = jupyter_manager.get_session(self.session_id)
            if not session:
                raise Exception(f"Session 不存在: {self.session_id}")
            
            # 执行代码（不做 check，直接执行）
            print(f"🔍 [Agent] 执行分析代码...")
            result = await session.execute_code(code, timeout=120)  # 增加超时时间
            print(f"🔍 [Agent] 执行完成：stdout={len(result.get('stdout', []))}, data={len(result.get('data', []))}, error={result.get('error')}")
            
            # 检查是否有错误（但仍然保留已生成的结果）
            if result['error']:
                error_info = result['error']
                # 如果有输出或图表，标记为部分成功
                has_output = bool(result['stdout'] or result['data'])
                if has_output:
                    step.status = "success"  # 有输出就算成功
                    print(f"⚠️ [Agent] 代码执行有错误，但已生成部分结果，继续处理")
                else:
                    step.status = "failed"
                    step.error = error_info
                
                # 组合 stdout 和 stderr
                output_lines = []
                if result['stdout']:
                    output_lines.append("=== 标准输出 ===")
                    output_lines.extend(result['stdout'])
                if result['stderr']:
                    output_lines.append("\n=== 错误输出 ===")
                    output_lines.extend(result['stderr'])
                if result['error'] and has_output:
                    output_lines.append(f"\n⚠️ 注意：代码执行过程中遇到错误: {error_info.get('evalue', '')}")
                
                step.output = '\n'.join(output_lines) if output_lines else "无输出"
                step.result = result  # 保存结果！
                logger.warning(f"代码执行有错误但已生成部分结果: {error_info.get('evalue', '未知错误')}")
            else:
                step.status = "success"
                # 组合所有输出
                output_lines = []
                
                # stdout
                if result['stdout']:
                    output_lines.append("=== 标准输出 ===")
                    output_lines.extend(result['stdout'])
                
                # display 数据
                if result['data']:
                    output_lines.append("\n=== 可视化输出 ===")
                    for idx, data_item in enumerate(result['data']):
                        data_content = data_item['data']
                        if 'text/plain' in data_content:
                            output_lines.append(f"\n[输出 {idx + 1}]")
                            output_lines.append(data_content['text/plain'])
                        if 'text/html' in data_content:
                            output_lines.append(f"\n[HTML 表格 {idx + 1}]")
                            output_lines.append("(HTML 表格已生成)")
                        if 'image/png' in data_content:
                            output_lines.append(f"\n[图表 {idx + 1}]")
                            output_lines.append("(图表已生成)")
                
                step.output = '\n'.join(output_lines) if output_lines else "✅ 代码执行成功（无输出）"
                step.result = result
                logger.info("代码执行成功")
        
        except Exception as e:
            logger.error(f"代码执行异常: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
        
        return step
    
    async def _fix_code(
        self,
        original_code: str,
        error: Dict,
        output: str
    ) -> AgentStep:
        """步骤3：修复代码"""
        step = AgentStep(
            title=f"修复代码（第{self.current_retry + 1}次尝试）",
            description="分析错误信息并修复代码",
            status="running"
        )
        
        try:
            logger.info(f"正在修复代码（第{self.current_retry + 1}次尝试）...")
            
            # 构建修复 prompt
            prompt = build_fix_prompt(
                user_request=self.user_request,
                selected_columns=self.selected_columns,
                original_code=original_code,
                error_info=error,
                output=output
            )
            
            # 调用 AI
            messages = [
                {"role": "system", "content": "你是一个专业的Python代码调试助手。"},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.3)
            
            # 提取修复后的代码
            fixed_code = self._extract_code_from_response(response)
            
            if not fixed_code:
                raise Exception("无法从 AI 响应中提取修复后的代码")
            
            step.code = fixed_code
            step.status = "success"
            step.output = "✅ 代码修复完成"
            
            logger.info("代码修复成功")
        
        except Exception as e:
            logger.error(f"代码修复失败: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
        
        return step
    
    async def _extract_result(
        self,
        output: str,
        exec_result: Dict
    ) -> AgentStep:
        """步骤3/4：提取结果"""
        step = AgentStep(
            title="提取结果",
            description="从执行输出中提取分析结果",
            status="running"
        )
        
        try:
            print(f"\n🔍 [提取结果] 输入参数：output长度={len(output) if output else 0}, exec_result keys={list(exec_result.keys()) if exec_result else None}")
            if exec_result:
                print(f"🔍 [提取结果] stdout={len(exec_result.get('stdout', []))}, data={len(exec_result.get('data', []))}")
            
            logger.info("正在提取结果...")
            
            result = {
                'data': [],
                'charts': [],
                'text': []
            }
            
            # 优先提取 stdout（真正的分析输出）
            if exec_result and exec_result.get('stdout'):
                # 合并所有 stdout
                full_text = ''.join(exec_result['stdout'])
                if full_text.strip():
                    result['text'].append(full_text)
                    print(f"✅ [提取结果] 提取到 stdout: {len(full_text)} 字符")
            
            # 提取执行结果中的图表和表格
            if exec_result and exec_result.get('data'):
                for data_item in exec_result['data']:
                    data_content = data_item['data']
                    
                    # 处理 HTML 表格
                    if 'text/html' in data_content:
                        html_content = data_content['text/html']
                        result['data'].append({
                            'type': 'html',
                            'content': html_content
                        })
                        logger.info(f"提取到 HTML 表格，长度: {len(html_content)}")
                    
                    # 处理图片
                    if 'image/png' in data_content:
                        result['charts'].append({
                            'type': 'image',
                            'format': 'png',
                            'data': data_content['image/png']
                        })
                        print(f"✅ [提取结果] 提取到图表")
                    
                    # 忽略 text/plain（因为真正的输出已经从 stdout 获取）
                    # text/plain 通常只是 (2527, 4) 这种无意义的输出
            
            # 清理空数组（但至少保留一个空结构避免完全为空）
            if not result['data']:
                del result['data']
            if not result['charts']:
                del result['charts']
            if not result['text']:
                del result['text']
            
            # 如果result完全为空，添加一个提示
            if not result:
                result['text'] = ["⚠️ 执行完成但未捕获到输出，请检查代码是否有 print 语句或图表生成"]
                print(f"⚠️ [提取结果] result 为空，添加提示信息")
            
            print(f"📦 [提取结果] 最终result keys={list(result.keys())}")
            
            self.final_result = result
            step.result = result
            step.status = "success"
            
            # 生成详细的输出信息
            output_parts = []
            if 'data' in result:
                output_parts.append(f"✅ 提取到 {len(result['data'])} 个数据表格")
            if 'charts' in result:
                output_parts.append(f"✅ 提取到 {len(result['charts'])} 个图表")
            if 'text' in result:
                output_parts.append(f"✅ 提取到文本输出")
            
            step.output = "\n".join(output_parts) if output_parts else "✅ 结果提取完成"
            
            logger.info(f"结果提取成功: {len(result)} 个项目")
        
        except Exception as e:
            logger.error(f"结果提取失败: {e}", exc_info=True)
            step.status = "failed"
            step.error = {"message": str(e)}
        
        return step
    
    async def _generate_summary(self) -> AgentStep:
        """步骤4/5：生成总结"""
        step = AgentStep(
            title="生成总结",
            description="使用 AI 生成分析结果总结",
            status="running"
        )
        
        try:
            print(f"\n🔍 [生成总结] final_result keys={list(self.final_result.keys()) if self.final_result else None}")
            if self.final_result:
                if 'text' in self.final_result:
                    print(f"🔍 [生成总结] text项数={len(self.final_result['text'])}, 前200字符={str(self.final_result['text'][:1])[:200]}")
                if 'charts' in self.final_result:
                    print(f"🔍 [生成总结] charts项数={len(self.final_result['charts'])}")
            
            logger.info("正在生成总结...")
            
            # 构建总结 prompt
            prompt = build_summary_prompt(
                user_request=self.user_request,
                result=self.final_result,
                code=self.steps[0].code if self.steps else ""
            )
            
            # 调用 AI
            messages = [
                {"role": "system", "content": "你是一个专业的数据分析师，擅长总结分析结果。"},
                {"role": "user", "content": prompt}
            ]
            
            summary = ai_client.chat(messages, temperature=0.7, max_tokens=1000)
            
            if self.final_result:
                self.final_result['summary'] = summary
            else:
                self.final_result = {'summary': summary}
            
            step.status = "success"
            step.output = summary
            
            logger.info("总结生成成功")
        
        except Exception as e:
            logger.error(f"总结生成失败: {e}")
            step.status = "failed"
            step.error = {"message": str(e)}
        
        return step
    
    def _extract_code_from_response(self, response: str) -> str:
        """从 AI 响应中提取 Python 代码"""
        # 匹配 ```python ... ``` 或 ``` ... ```
        pattern = r'```(?:python)?\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # 如果没有代码块，尝试提取整个响应
        return response.strip()
    
    def _build_response(self) -> Dict[str, Any]:
        """构建响应"""
        return {
            "status": self.status,
            "data": {
                "steps": [step.to_dict() for step in self.steps],
                "result": self.final_result,
                "error": self.error_message
            }
        }
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self._build_response()

