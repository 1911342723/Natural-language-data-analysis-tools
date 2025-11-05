"""
AI 客户端封装（支持 OpenAI 和 Anthropic）
"""
import logging
from typing import List, Dict
from config import settings

logger = logging.getLogger(__name__)


class AIClient:
    """AI 客户端统一接口"""
    
    def __init__(self):
        self.provider = settings.ai_provider
        
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            self.model = settings.openai_model
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
        else:
            raise ValueError(f"不支持的 AI 提供商: {self.provider}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        调用 AI 聊天接口（非流式）
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            AI 响应文本
        """
        try:
            logger.info(f"🤖 调用AI: provider={self.provider}, model={self.model}")
            logger.debug(f"📝 消息内容: {messages}")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                result = response.choices[0].message.content
                logger.info(f"✅ AI响应成功，长度: {len(result)} 字符")
                return result
            
            elif self.provider == "anthropic":
                # Anthropic 的消息格式略有不同
                system_message = None
                user_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message,
                    messages=user_messages,
                )
                return response.content[0].text
        
        except Exception as e:
            logger.error(f"AI 调用失败: {e}")
            raise Exception(f"AI 调用失败: {str(e)}")
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        """
        调用 AI 聊天接口（流式）
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Yields:
            逐个 token 的文本片段
        """
        try:
            if self.provider == "openai":
                logger.info(f"🌊 开始流式调用: model={self.model}, base_url={self.client.base_url}")
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                chunk_count = 0
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        chunk_count += 1
                        content = chunk.choices[0].delta.content
                        # print(f"📤 收到 chunk #{chunk_count}: {repr(content[:50])}")  # 调试输出（已禁用）
                        yield content
                # logger.info(f"✅ 流式调用完成，共收到 {chunk_count} 个 chunks")  # 调试日志（已禁用）
            
            elif self.provider == "anthropic":
                # Anthropic 的消息格式略有不同
                system_message = None
                user_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)
                
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message,
                    messages=user_messages,
                ) as stream:
                    for text in stream.text_stream:
                        yield text
        
        except Exception as e:
            logger.error(f"AI 流式调用失败: {e}")
            raise Exception(f"AI 流式调用失败: {str(e)}")


# 全局 AI 客户端
ai_client = AIClient()


