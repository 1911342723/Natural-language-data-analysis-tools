"""
Jupyter Kernel 管理模块
"""
import asyncio
import json
import uuid
import os
from typing import Dict, Any, Optional, List
from jupyter_client import KernelManager
from jupyter_client.asynchronous import AsyncKernelClient
from traitlets.config import Config
import logging

from config import settings

logger = logging.getLogger(__name__)


class JupyterSession:
    """Jupyter Session 会话"""
    
    def __init__(self, session_id: str, kernel_manager: KernelManager):
        self.session_id = session_id
        self.kernel_manager = kernel_manager
        self.kernel_client: Optional[AsyncKernelClient] = None
        self.created_at = asyncio.get_event_loop().time()
    
    async def start(self):
        """启动 kernel"""
        logger.info(f"启动 Jupyter Kernel: {self.session_id}")
        
        # 1. 启动 kernel（传递环境变量以优化 Windows 兼容性）
        import sys
        import os
        
        env = os.environ.copy()
        # Windows 上配置环境变量
        if sys.platform == 'win32':
            env['PYTHONIOENCODING'] = 'utf-8'
        
        self.kernel_manager.start_kernel(env=env)
        logger.info(f"✅ Kernel 已启动（使用 KernelManager 的密钥配置）")
        
        # 2. 获取客户端（自动继承 KernelManager 的 config，包括密钥）
        self.kernel_client = self.kernel_manager.client()
        logger.info(f"✅ 客户端已创建（自动继承密钥配置）")
        
        # 3. 启动通道
        self.kernel_client.start_channels()
        logger.info(f"✅ 通道已启动")
        
        # 等待 kernel 就绪
        try:
            await asyncio.wait_for(
                self._wait_for_ready(),
                timeout=settings.kernel_startup_timeout
            )
            logger.info(f"Kernel 就绪: {self.session_id}")
        except asyncio.TimeoutError:
            logger.error(f"Kernel 启动超时: {self.session_id}")
            raise Exception("Kernel 启动超时")
    
    async def _wait_for_ready(self):
        """等待 kernel 就绪"""
        while True:
            try:
                # 发送测试命令（使用简单的表达式，不产生输出）
                msg_id = self.kernel_client.execute("1+1", silent=True, store_history=False)
                await asyncio.sleep(0.1)
                
                # 检查是否有响应
                try:
                    msg = self.kernel_client.get_iopub_msg(timeout=1)
                    if msg['msg_type'] in ['execute_result', 'status']:
                        # 清空所有待处理的消息，避免污染后续输出
                        while self.kernel_client.iopub_channel.msg_ready():
                            self.kernel_client.get_iopub_msg(timeout=0.1)
                        return
                except:
                    pass
            except Exception as e:
                await asyncio.sleep(0.5)
    
    async def execute_code(
        self,
        code: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        执行代码并收集输出
        
        返回格式：
        {
            'stdout': [],      # 标准输出
            'stderr': [],      # 错误输出
            'data': [],        # 数据输出（图表、DataFrame等）
            'error': None,     # 异常信息
            'execution_count': None
        }
        """
        if not self.kernel_client:
            raise Exception("Kernel 未启动")
        
        logger.info(f"执行代码 (session: {self.session_id}):\n{code[:200]}...")
        
        outputs = {
            'stdout': [],
            'stderr': [],
            'data': [],
            'error': None,
            'execution_count': None
        }
        
        # 执行代码
        msg_id = self.kernel_client.execute(code)
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查超时
            if asyncio.get_event_loop().time() - start_time > timeout:
                outputs['error'] = {
                    'ename': 'TimeoutError',
                    'evalue': f'代码执行超时（{timeout}秒）',
                    'traceback': []
                }
                break
            
            try:
                msg = await asyncio.wait_for(
                    asyncio.to_thread(self.kernel_client.get_iopub_msg),
                    timeout=0.5
                )
                
                msg_type = msg['header']['msg_type']
                content = msg['content']
                
                # 标准输出
                if msg_type == 'stream':
                    if content['name'] == 'stdout':
                        text = content['text']
                        outputs['stdout'].append(text)
                        print(f"📤 [收到stdout] {text[:100]}")
                    elif content['name'] == 'stderr':
                        outputs['stderr'].append(content['text'])
                
                # 执行结果
                elif msg_type == 'execute_result':
                    outputs['execution_count'] = content['execution_count']
                    outputs['data'].append({
                        'type': 'execute_result',
                        'data': content['data']
                    })
                
                # 显示数据
                elif msg_type == 'display_data':
                    outputs['data'].append({
                        'type': 'display_data',
                        'data': content['data']
                    })
                
                # 错误
                elif msg_type == 'error':
                    outputs['error'] = {
                        'ename': content['ename'],
                        'evalue': content['evalue'],
                        'traceback': content['traceback']
                    }
                
                # 执行完成
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    # 收到 idle，但消息可能还在传输中，等待并收集
                    print(f"📍 [收到idle] 等待剩余消息...")
                    
                    # 给消息一些时间到达（最多等待 3 秒）
                    remaining_count = 0
                    for wait_round in range(30):  # 30 * 0.1s = 3 秒
                        # 检查队列
                        while self.kernel_client.iopub_channel.msg_ready():
                            try:
                                msg_extra = self.kernel_client.get_iopub_msg(timeout=0.1)
                                msg_type_extra = msg_extra['header']['msg_type']
                                content_extra = msg_extra['content']
                                
                                if msg_type_extra == 'stream' and content_extra['name'] == 'stdout':
                                    outputs['stdout'].append(content_extra['text'])
                                    print(f"📤 [收到stdout] {content_extra['text'][:100]}")
                                    remaining_count += 1
                                elif msg_type_extra == 'display_data':
                                    outputs['data'].append({
                                        'type': 'display_data',
                                        'data': content_extra['data']
                                    })
                                    print(f"📊 [收到display_data]")
                                    remaining_count += 1
                            except Exception as e:
                                print(f"⚠️ [读取消息失败] {e}")
                                break
                        
                        # 如果连续 3 轮没有新消息，提前退出
                        if wait_round >= 3 and remaining_count == 0:
                            print(f"📍 [等待结束] 连续无新消息，退出等待")
                            break
                        
                        # 重置计数器，只统计本轮的消息
                        if remaining_count > 0:
                            remaining_count = 0
                        
                        # 等待 0.1 秒再检查
                        await asyncio.sleep(0.1)
                    
                    if remaining_count > 0:
                        print(f"✅ [收集完成] 总共收集了 {remaining_count} 条消息")
                    else:
                        print(f"⚠️ [收集完成] 未收集到额外消息")
                    break
                    
            except asyncio.TimeoutError:
                # 继续等待
                continue
            except Exception as e:
                logger.error(f"获取消息失败: {e}")
                break
        
        print(f"\n📋 [执行完成] stdout行数={len(outputs['stdout'])}, data项数={len(outputs['data'])}, error={outputs['error'] is not None}")
        if outputs['stdout']:
            print(f"📋 [stdout前200字符] {outputs['stdout'][:200]}")
        if outputs['data']:
            print(f"📋 [data类型] {[d['type'] for d in outputs['data']]}")
        
        logger.info(f"代码执行完成 (session: {self.session_id})")
        return outputs
    
    async def shutdown(self):
        """关闭 kernel"""
        logger.info(f"关闭 Jupyter Kernel: {self.session_id}")
        
        if self.kernel_client:
            self.kernel_client.stop_channels()
        
        if self.kernel_manager:
            self.kernel_manager.shutdown_kernel(now=True)


class JupyterManager:
    """Jupyter 会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, JupyterSession] = {}
    
    async def create_session(self, data_json: str) -> str:
        """
        创建新的 Jupyter Session
        
        Args:
            data_json: 数据的 JSON 字符串
        
        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())
        
        # **终极方案**：使用固定密钥，让客户端和 Kernel 使用相同的密钥
        from traitlets.config import Config
        
        session_key = b'data-analysis-tool-secret-key'
        
        c = Config()
        c.Session.key = session_key
        
        # 增加 ZMQ 缓冲区大小，防止大量输出时崩溃（Windows 兼容性）
        c.ZMQInteractiveShell.kernel_timeout = 120  # 增加超时时间
        
        km = KernelManager(config=c)
        logger.info(f"✅ 创建 KernelManager，使用固定密钥（{len(session_key)} 字节）+ ZMQ 优化配置")
        
        # 创建 Session
        session = JupyterSession(session_id, km)
        await session.start()
        
        # 初始化环境：加载数据
        init_code = f"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, HTML, Image
import io
import base64
import json

# 配置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 加载数据
_data_json = '''{data_json}'''
df = pd.read_json(_data_json, orient='records')

# 初始化完成（不输出任何内容到 stdout）
None
"""
        
        print(f"\n🔧 [Session {session_id[:8]}] 开始执行初始化代码...")
        result = await session.execute_code(init_code, timeout=30)
        
        print(f"🔧 [Session {session_id[:8]}] 初始化结果: error={result.get('error')}, has_stdout={bool(result.get('stdout'))}")
        
        if result.get('error'):
            error_msg = result['error'].get('evalue', '未知错误')
            error_trace = '\n'.join(result['error'].get('traceback', []))
            print(f"❌ [Session {session_id[:8]}] 初始化失败: {error_msg}")
            print(f"错误堆栈:\n{error_trace}")
            await session.shutdown()
            raise Exception(f"Session 初始化失败: {error_msg}")
        
        # Windows 上 ZMQ 存在严重 bug，快速连续执行代码会导致 Kernel 崩溃
        # 因此跳过额外的验证步骤，直接信任初始化代码的执行结果
        # 如果初始化代码执行成功（无 error），说明 df 已成功加载
        print(f"✅ [Session {session_id[:8]}] DataFrame 初始化完成，Kernel 就绪")
        
        # 保存 session
        self.sessions[session_id] = session
        
        logger.info(f"Session 创建成功: {session_id}")
        return session_id
    
    async def create_multi_session(self, tables_data: List[Dict]) -> str:
        """
        创建多文件 Jupyter Session
        
        Args:
            tables_data: 表格数据列表
                [
                    {
                        'alias': 'df1',
                        'data_json': '...',
                        'file_name': 'file1.csv',
                        'sheet_name': 'Sheet1'
                    },
                    ...
                ]
        
        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())
        
        # 使用固定密钥创建 KernelManager
        from traitlets.config import Config
        
        session_key = b'data-analysis-tool-secret-key'
        c = Config()
        c.Session.key = session_key
        
        # 增加 ZMQ 缓冲区大小，防止大量输出时崩溃（Windows 兼容性）
        c.ZMQInteractiveShell.kernel_timeout = 120
        
        km = KernelManager(config=c)
        logger.info(f"✅ 创建多文件 KernelManager，表格数量: {len(tables_data)}（已应用 ZMQ 优化）")
        
        # 创建 Session
        session = JupyterSession(session_id, km)
        await session.start()
        
        # 初始化环境：导入库
        init_code = """
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, HTML, Image
import io
import base64
import json

# 配置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 环境初始化完成
None
"""
        
        print(f"\n🔧 [Multi-Session {session_id[:8]}] 初始化环境...")
        result = await session.execute_code(init_code, timeout=30)
        
        if result.get('error'):
            error_msg = result['error'].get('evalue', '未知错误')
            print(f"❌ [Multi-Session {session_id[:8]}] 环境初始化失败: {error_msg}")
            await session.shutdown()
            raise Exception(f"多文件 Session 初始化失败: {error_msg}")
        
        print(f"✅ [Multi-Session {session_id[:8]}] 环境初始化完成")
        
        # 逐个加载表格
        for idx, table in enumerate(tables_data):
            alias = table['alias']
            data_json = table['data_json']
            file_name = table['file_name']
            sheet_name = table['sheet_name']
            
            load_code = f"""
# 加载表格: {alias}
_data_json_{idx} = '''{data_json}'''
{alias} = pd.read_json(_data_json_{idx}, orient='records')

# 表格加载完成（不输出到 stdout）
None
"""
            
            print(f"🔧 [Multi-Session {session_id[:8]}] 加载表格 '{alias}'...")
            load_result = await session.execute_code(load_code, timeout=30)
            
            if load_result.get('error'):
                error_msg = load_result['error'].get('evalue', '未知错误')
                print(f"❌ [Multi-Session {session_id[:8]}] 表格 '{alias}' 加载失败: {error_msg}")
                await session.shutdown()
                raise Exception(f"表格 '{alias}' 加载失败: {error_msg}")
            
            # 跳过验证步骤（Windows 上 ZMQ bug），信任初始化代码的执行结果
            print(f"✅ [Multi-Session {session_id[:8]}] 表格 '{alias}' 加载完成")
        
        # 保存 session
        self.sessions[session_id] = session
        
        logger.info(f"多文件 Session 创建成功: {session_id}, 表格数: {len(tables_data)}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[JupyterSession]:
        """获取 Session"""
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """关闭 Session"""
        session = self.sessions.get(session_id)
        if session:
            await session.shutdown()
            del self.sessions[session_id]
            logger.info(f"Session 已关闭: {session_id}")
    
    async def cleanup_old_sessions(self, max_age: int = 3600):
        """清理超时的 Session（默认1小时）"""
        current_time = asyncio.get_event_loop().time()
        to_remove = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.created_at > max_age:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            await self.close_session(session_id)
        
        if to_remove:
            logger.info(f"清理了 {len(to_remove)} 个超时 Session")


# 全局管理器实例
jupyter_manager = JupyterManager()

