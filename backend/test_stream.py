"""
测试 AI 流式调用
用于诊断流式调用是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.ai_client import ai_client
import asyncio

async def test_stream():
    """测试流式调用"""
    print("=" * 60)
    print("🧪 开始测试 AI 流式调用")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "请用Python写一个简单的Hello World程序，包含注释"}
    ]
    
    print("\n📝 测试消息:", messages[0]['content'])
    print("\n🌊 开始流式接收...\n")
    
    full_response = ""
    chunk_count = 0
    
    try:
        for chunk in ai_client.chat_stream(messages, temperature=0.7):
            chunk_count += 1
            full_response += chunk
            print(f"Chunk #{chunk_count}: {repr(chunk)}")
            
        print("\n" + "=" * 60)
        print(f"✅ 流式调用完成！")
        print(f"✅ 总共收到 {chunk_count} 个 chunks")
        print(f"✅ 总长度: {len(full_response)} 字符")
        print("=" * 60)
        print("\n完整响应:")
        print(full_response)
        
        if chunk_count == 0:
            print("\n❌ 警告: 没有收到任何流式 chunks!")
            print("可能的原因:")
            print("1. API Key 无效")
            print("2. Base URL 配置错误")
            print("3. 网络连接问题")
            print("4. AI 提供商不支持流式调用")
        elif chunk_count == 1:
            print("\n⚠️  警告: 只收到 1 个 chunk，流式效果不明显")
            print("可能的原因:")
            print("1. AI 响应太短")
            print("2. 流式调用配置有问题")
        else:
            print(f"\n✅ 流式调用正常！收到 {chunk_count} 个 chunks")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stream())

