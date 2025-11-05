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
        
        # 3. 启动通道，并设置 ZMQ socket 选项（增强稳定性）
        self.kernel_client.start_channels()
        
        # 设置 ZMQ socket 参数（防止大消息导致崩溃）
        try:
            import zmq
            # 增加接收缓冲区大小到 50MB
            if hasattr(self.kernel_client, 'iopub_channel') and hasattr(self.kernel_client.iopub_channel, 'socket'):
                socket = self.kernel_client.iopub_channel.socket
                if socket:
                    socket.setsockopt(zmq.RCVHWM, 0)  # 无限制高水位标记
                    socket.setsockopt(zmq.SNDHWM, 0)  # 无限制高水位标记
                    logger.info(f"✅ ZMQ socket 参数已优化")
        except Exception as e:
            logger.warning(f"⚠️ 无法设置 ZMQ socket 参数: {e}")
        
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
        timeout: int = 600  # 设置一个很大的兜底超时（10分钟），仅用于防止死循环
    ) -> Dict[str, Any]:
        """
        智能执行代码并收集输出（不依赖固定超时，基于 Kernel 状态判断）
        
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
        
        # 检查 Kernel 是否存活
        if not self.kernel_manager.is_alive():
            outputs['error'] = {
                'ename': 'KernelError',
                'evalue': 'Kernel 已崩溃或异常退出，请重新上传文件',
                'traceback': ['提示：如果图表 DPI 过高（如300），可能导致内存不足。建议降低 DPI 或简化数据。']
            }
            logger.error(f"❌ Kernel 已死亡: {self.session_id}")
            return outputs
        
        # 执行代码
        try:
            msg_id = self.kernel_client.execute(code)
        except Exception as e:
            outputs['error'] = {
                'ename': 'ExecutionError',
                'evalue': f'代码执行失败: {str(e)}',
                'traceback': [str(e)]
            }
            logger.error(f"❌ 执行代码失败: {e}")
            return outputs
        
        start_time = asyncio.get_event_loop().time()
        last_progress_time = start_time
        
        while True:
            # 极限超时保护（仅用于防止死循环，正常情况不应触发）
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > timeout:
                logger.warning(f"⚠️ 触发极限超时保护（{timeout}秒），可能遇到死循环")
                outputs['error'] = {
                    'ename': 'ExtremeLimitError',
                    'evalue': f'执行时间超过极限保护时间（{timeout}秒），已强制中断',
                    'traceback': ['提示：这通常表示代码陷入死循环，请检查代码逻辑']
                }
                break
            
            # 每30秒打印一次进度日志（让用户知道还在执行，没有卡住）
            if elapsed_time - last_progress_time >= 30:
                print(f"⏳ [执行进度] 已运行 {int(elapsed_time)} 秒，Kernel 仍在处理中...")
                logger.info(f"代码执行中... 已耗时 {int(elapsed_time)} 秒")
                last_progress_time = elapsed_time
            
            # 定期检查 Kernel 健康状态
            current_time = asyncio.get_event_loop().time()
            if int(current_time - start_time) % 10 < 0.5:  # 每10秒检查一次
                if not self.kernel_manager.is_alive():
                    outputs['error'] = {
                        'ename': 'KernelCrashed',
                        'evalue': 'Kernel 在执行过程中崩溃',
                        'traceback': ['可能原因：内存不足、图表 DPI 过高、数据量过大']
                    }
                    logger.error(f"❌ Kernel 崩溃: {self.session_id}")
                    break
            
            try:
                msg = await asyncio.wait_for(
                    asyncio.to_thread(self.kernel_client.get_iopub_msg),
                    timeout=0.5
                )
                
                # 安全地提取消息类型和内容
                if not isinstance(msg, dict):
                    logger.warning(f"收到非字典类型的消息: {type(msg)}")
                    continue
                
                if 'header' not in msg or 'msg_type' not in msg.get('header', {}):
                    logger.warning(f"消息缺少 header 或 msg_type: {msg.keys()}")
                    continue
                
                if 'content' not in msg:
                    logger.warning(f"消息缺少 content")
                    continue
                
                msg_type = msg['header']['msg_type']
                content = msg['content']
                
                # 记录所有非 status/execute_input 消息
                if msg_type not in ['status', 'execute_input']:
                    print(f"🔍 [消息类型] {msg_type}")
                
                # 标准输出
                if msg_type == 'stream':
                    if content['name'] == 'stdout':
                        text = content['text']
                        outputs['stdout'].append(text)
                        print(f"📤 [收到stdout] {text[:100]}")
                    elif content['name'] == 'stderr':
                        stderr_text = content['text']
                        outputs['stderr'].append(stderr_text)
                        print(f"⚠️ [收到stderr] {stderr_text[:200]}")
                
                # 执行结果
                elif msg_type == 'execute_result':
                    outputs['execution_count'] = content['execution_count']
                    outputs['data'].append({
                        'type': 'execute_result',
                        'data': content['data']
                    })
                    print(f"📊 [收到execute_result] execution_count={content['execution_count']}")
                
                # 显示数据
                elif msg_type == 'display_data':
                    outputs['data'].append({
                        'type': 'display_data',
                        'data': content['data']
                    })
                    print(f"📊 [收到display_data] data keys={list(content.get('data', {}).keys())}")
                
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
                    
                    # 给消息一些时间到达（最多等待 5 秒）
                    total_collected = 0
                    empty_rounds = 0  # 连续空轮次计数
                    
                    for wait_round in range(50):  # 50 * 0.1s = 5 秒
                        collected_this_round = 0
                        
                        # 先等待一小段时间，让消息有机会到达
                        await asyncio.sleep(0.1)
                        
                        # 检查队列
                        while self.kernel_client.iopub_channel.msg_ready():
                            try:
                                msg_extra = self.kernel_client.get_iopub_msg(timeout=0.1)
                                
                                # 验证消息格式
                                if not isinstance(msg_extra, dict):
                                    continue
                                if 'header' not in msg_extra or 'msg_type' not in msg_extra.get('header', {}):
                                    continue
                                if 'content' not in msg_extra:
                                    continue
                                
                                msg_type_extra = msg_extra['header']['msg_type']
                                content_extra = msg_extra['content']
                                
                                if msg_type_extra == 'stream' and content_extra.get('name') == 'stdout':
                                    if 'text' in content_extra:
                                        outputs['stdout'].append(content_extra['text'])
                                        print(f"📤 [收到stdout] {content_extra['text'][:100]}")
                                        collected_this_round += 1
                                elif msg_type_extra == 'display_data':
                                    if 'data' in content_extra:
                                        outputs['data'].append({
                                            'type': 'display_data',
                                            'data': content_extra['data']
                                        })
                                        print(f"📊 [收到display_data]")
                                        collected_this_round += 1
                                elif msg_type_extra == 'execute_result':
                                    if 'data' in content_extra:
                                        outputs['data'].append({
                                            'type': 'execute_result',
                                            'data': content_extra['data']
                                        })
                                        print(f"📊 [收到execute_result]")
                                        collected_this_round += 1
                            except Exception as e:
                                if "Invalid Signature" not in str(e):
                                    print(f"⚠️ [读取消息失败] {type(e).__name__}: {e}")
                                # 跳过错误消息，继续处理下一条
                                continue
                        
                        total_collected += collected_this_round
                        
                        # 如果本轮没有收到消息
                        if collected_this_round == 0:
                            empty_rounds += 1
                            # 连续 10 轮（1秒）没有新消息，且已经收到过一些消息，则退出
                            if empty_rounds >= 10 and total_collected > 0:
                                print(f"📍 [等待结束] 连续 {empty_rounds} 轮无新消息，已收集 {total_collected} 条")
                                break
                            # 如果前 15 轮都没消息，也退出（可能本来就没输出）
                            if empty_rounds >= 15:
                                print(f"📍 [等待结束] {empty_rounds} 轮均无消息")
                                break
                        else:
                            # 收到消息，重置空轮次计数
                            empty_rounds = 0
                    
                    if total_collected > 0:
                        print(f"✅ [收集完成] 总共收集了 {total_collected} 条消息")
                    else:
                        print(f"⚠️ [收集完成] 未收集到额外消息")
                    break
                    
            except asyncio.TimeoutError:
                # 继续等待
                continue
            except Exception as e:
                # Invalid Signature 错误不影响功能，只记录调试信息
                if "Invalid Signature" in str(e):
                    logger.debug(f"消息签名验证失败（不影响功能）: {e}")
                else:
                    # 记录错误但继续处理后续消息
                    logger.error(f"获取消息失败: {type(e).__name__}: {e}")
                    print(f"⚠️ [消息处理错误] {type(e).__name__}: {e}")
                # 继续处理后续消息而不是中断
                continue
        
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
        
        try:
            # 1. 停止客户端通道
            if self.kernel_client:
                self.kernel_client.stop_channels()
                logger.info(f"✅ 客户端通道已停止")
            
            # 2. 关闭 kernel manager
            if self.kernel_manager and self.kernel_manager.is_alive():
                self.kernel_manager.shutdown_kernel(now=False, restart=False)
                logger.info(f"✅ Kernel 已关闭")
        except Exception as e:
            logger.error(f"关闭 Kernel 时出错: {e}")
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
        import tempfile
        
        session_id = str(uuid.uuid4())
        
        # **终极方案**：使用固定密钥，让客户端和 Kernel 使用相同的密钥
        from traitlets.config import Config
        
        session_key = b'data-analysis-tool-secret-key'
        
        c = Config()
        c.Session.key = session_key
        
        # 增加 ZMQ 缓冲区大小和消息限制（防止大图表导致崩溃）
        c.ZMQInteractiveShell.kernel_timeout = 120  # 增加超时时间
        
        # ZMQ 消息大小限制（50MB，足够容纳高 DPI 图表）
        import zmq
        c.Session.buffer_threshold = 50 * 1024 * 1024  # 50MB
        c.Session.copy_threshold = 50 * 1024 * 1024   # 50MB
        
        km = KernelManager(config=c)
        
        # 设置 Kernel 启动参数（增加内存限制和稳定性）
        km.kernel_spec_manager.whitelist = set()
        
        logger.info(f"✅ 创建 KernelManager，使用固定密钥（{len(session_key)} 字节）+ ZMQ 优化配置（50MB 缓冲）")
        
        # 创建 Session
        session = JupyterSession(session_id, km)
        await session.start()
        
        # 初始化环境：加载数据
        init_code = """
import sys
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

# 预导入科研库（捕获导入错误）
try:
    from scipy import stats
    import scipy
    from sklearn.linear_model import LinearRegression
    import sklearn
    print("✅ 科研库导入成功: scipy, sklearn", file=sys.stderr)
except ImportError as e:
    print(f"⚠️ 科研库导入失败: {e}", file=sys.stderr)
    print("提示：请运行 pip install scipy scikit-learn", file=sys.stderr)

# 配置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 加载数据
{data_load_code}

# 初始化完成（不输出任何内容到 stdout）
None
"""
        
        # 计算数据大小
        data_size_mb = len(data_json) / (1024 * 1024)
        
        # 对于大文件（> 10MB），使用临时文件传输
        if data_size_mb > 10:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
            temp_file.write(data_json)
            temp_file.close()
            temp_path = temp_file.name
            
            # 使用文件路径加载（Windows 路径需要转义）
            escaped_path = temp_path.replace('\\', '\\\\')
            
            data_load_code = f"""
# 使用临时文件加载大数据（避免 ZMQ 消息过大）
df = pd.read_json(r'{escaped_path}', orient='records')

# 清理临时文件
import os
try:
    os.unlink(r'{escaped_path}')
except:
    pass
"""
            print(f"\n🔧 [Session {session_id[:8]}] 开始执行初始化代码... (数据大小: {data_size_mb:.2f} MB, 使用临时文件)")
        else:
            # 小文件直接嵌入代码
            data_load_code = f"""
_data_json = '''{data_json}'''
df = pd.read_json(_data_json, orient='records')
"""
            print(f"\n🔧 [Session {session_id[:8]}] 开始执行初始化代码... (数据大小: {data_size_mb:.2f} MB)")
        
        # 替换模板中的数据加载代码
        init_code = init_code.replace('{data_load_code}', data_load_code)
        
        result = await session.execute_code(init_code)  # 使用默认的智能执行（基于 Kernel 状态，不依赖固定超时）
        
        print(f"🔧 [Session {session_id[:8]}] 初始化结果: error={result.get('error')}, has_stdout={bool(result.get('stdout'))}, has_stderr={bool(result.get('stderr'))}")
        
        # 输出 stderr 信息（导入错误等）
        if result.get('stderr'):
            for stderr_line in result.get('stderr'):
                print(f"  ⚠️ stderr: {stderr_line.strip()}")
        
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
        result = await session.execute_code(init_code)  # 使用智能执行（基于 Kernel 状态）
        
        if result.get('error'):
            error_msg = result['error'].get('evalue', '未知错误')
            print(f"❌ [Multi-Session {session_id[:8]}] 环境初始化失败: {error_msg}")
            await session.shutdown()
            raise Exception(f"多文件 Session 初始化失败: {error_msg}")
        
        print(f"✅ [Multi-Session {session_id[:8]}] 环境初始化完成")
        
        # 逐个加载表格
        import tempfile
        import os
        
        for idx, table in enumerate(tables_data):
            alias = table['alias']
            data_json = table['data_json']
            file_name = table['file_name']
            sheet_name = table['sheet_name']
            
            # 计算数据大小（用于日志）
            data_size_mb = len(data_json) / (1024 * 1024)
            
            # 对于大文件（> 10MB），使用临时文件传输，避免 ZMQ 消息队列崩溃
            if data_size_mb > 10:
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
                temp_file.write(data_json)
                temp_file.close()
                temp_path = temp_file.name
                
                # 使用文件路径加载（Windows 路径需要转义）
                escaped_path = temp_path.replace('\\', '\\\\')
                
                load_code = f"""
# 加载表格: {alias} (使用临时文件，避免 ZMQ 消息过大)
{alias} = pd.read_json(r'{escaped_path}', orient='records')

# 清理临时文件
import os
try:
    os.unlink(r'{escaped_path}')
except:
    pass

# 表格加载完成（不输出到 stdout）
None
"""
                print(f"🔧 [Multi-Session {session_id[:8]}] 加载表格 '{alias}' (文件: {file_name}, 数据大小: {data_size_mb:.2f} MB, 使用临时文件)...")
            else:
                # 小文件直接嵌入代码
                load_code = f"""
# 加载表格: {alias}
_data_json_{idx} = '''{data_json}'''
{alias} = pd.read_json(_data_json_{idx}, orient='records')

# 表格加载完成（不输出到 stdout）
None
"""
                print(f"🔧 [Multi-Session {session_id[:8]}] 加载表格 '{alias}' (文件: {file_name}, 数据大小: {data_size_mb:.2f} MB)...")
            
            load_result = await session.execute_code(load_code)  # 智能执行，自动适应文件大小
            
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

