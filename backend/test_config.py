"""
配置检查和测试脚本
运行此脚本验证配置是否正确加载
"""
import os
import sys

print("=" * 60)
print("📋 配置检查工具")
print("=" * 60)

# 检查 .env 文件
env_file = ".env"
if os.path.exists(env_file):
    print(f"\n✅ 找到 .env 文件: {os.path.abspath(env_file)}")
else:
    print(f"\n❌ 未找到 .env 文件")
    print(f"   请在 backend 目录下创建 .env 文件")
    sys.exit(1)

# 读取 .env 文件（不显示完整密钥）
print(f"\n📄 .env 文件内容:")
with open(env_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                key, value = line.split('=', 1)
                if 'KEY' in key.upper():
                    if value:
                        print(f"   {key}={value[:10]}...{value[-4:]}")
                    else:
                        print(f"   {key}=(空)")
                else:
                    print(f"   {key}={value}")

print("\n" + "-" * 60)

# 加载配置
try:
    from config import settings
    print("\n✅ 配置类加载成功")
except Exception as e:
    print(f"\n❌ 配置加载失败: {e}")
    sys.exit(1)

# 显示配置
print(f"\n🤖 AI 配置:")
print(f"   提供商: {settings.ai_provider}")

if settings.ai_provider == "openai":
    api_key = settings.openai_api_key
    if api_key:
        print(f"   ✅ API Key: {api_key[:10]}...{api_key[-4:]} (长度: {len(api_key)})")
    else:
        print(f"   ❌ API Key: 未设置或为空")
    print(f"   Base URL: {settings.openai_base_url}")
    print(f"   模型: {settings.openai_model}")
elif settings.ai_provider == "anthropic":
    api_key = settings.anthropic_api_key
    if api_key:
        print(f"   ✅ API Key: {api_key[:10]}...{api_key[-4:]}")
    else:
        print(f"   ❌ API Key: 未设置")
    print(f"   模型: {settings.anthropic_model}")

print(f"\n💾 其他配置:")
print(f"   数据库: {settings.database_url}")
print(f"   上传目录: {settings.upload_dir}")
print(f"   文件大小限制: {settings.max_file_size / 1024 / 1024:.0f}MB")

print("\n" + "=" * 60)
print("\n🧪 测试 AI 连接...")

try:
    from core.ai_client import ai_client
    print(f"   正在调用 {settings.ai_provider} API...")
    response = ai_client.chat([
        {"role": "user", "content": "请回复'连接成功'"}
    ])
    print(f"   ✅ 连接成功！")
    print(f"   AI 回复: {response[:100]}...")
except Exception as e:
    print(f"   ❌ 连接失败: {str(e)}")
    print(f"\n💡 排查建议:")
    print(f"   1. 检查 .env 文件中的 AI_PROVIDER 是否为 'openai'")
    print(f"   2. 检查 OPENAI_API_KEY 是否正确（DeepSeek 的 key）")
    print(f"   3. 检查 OPENAI_BASE_URL 是否为 'https://api.deepseek.com'")
    print(f"   4. 重启后端服务使配置生效")

print("\n" + "=" * 60)


