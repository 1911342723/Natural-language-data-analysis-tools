"""
检查配置是否正确
运行此脚本验证 .env 配置
"""
from config import settings
import sys


def check_config():
    """检查配置"""
    print("=" * 60)
    print("🔍 检查配置...")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 1. 检查 API 配置
    print("\n📡 API 配置:")
    print(f"  Host: {settings.api_host}")
    print(f"  Port: {settings.api_port}")
    print(f"  Debug: {settings.debug}")
    
    # 2. 检查 AI 配置
    print("\n🤖 AI 配置:")
    print(f"  提供商: {settings.ai_provider}")
    
    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            errors.append("❌ OPENAI_API_KEY 未配置")
        else:
            key_preview = f"{settings.openai_api_key[:10]}...{settings.openai_api_key[-4:]}"
            print(f"  API Key: {key_preview}")
        
        print(f"  模型: {settings.openai_model}")
        print(f"  Base URL: {settings.openai_base_url}")
        
        # 检测使用的是哪个服务
        if "deepseek" in settings.openai_base_url.lower():
            print(f"  ✅ 使用 DeepSeek API")
        elif "openai.com" in settings.openai_base_url.lower():
            print(f"  ✅ 使用 OpenAI 官方 API")
        else:
            warnings.append(f"⚠️  使用自定义 API: {settings.openai_base_url}")
    
    elif settings.ai_provider == "anthropic":
        if not settings.anthropic_api_key:
            errors.append("❌ ANTHROPIC_API_KEY 未配置")
        else:
            key_preview = f"{settings.anthropic_api_key[:10]}...{settings.anthropic_api_key[-4:]}"
            print(f"  API Key: {key_preview}")
        
        print(f"  模型: {settings.anthropic_model}")
        print(f"  ✅ 使用 Anthropic Claude API")
    
    # 3. 检查数据库配置
    print("\n💾 数据库配置:")
    print(f"  URL: {settings.database_url}")
    
    # 4. 检查文件上传配置
    print("\n📁 文件上传配置:")
    print(f"  目录: {settings.upload_dir}")
    print(f"  最大大小: {settings.max_file_size / 1024 / 1024:.0f}MB")
    
    # 5. 检查 Jupyter 配置
    print("\n📓 Jupyter 配置:")
    print(f"  执行超时: {settings.jupyter_timeout}秒")
    print(f"  启动超时: {settings.kernel_startup_timeout}秒")
    
    # 6. 检查安全配置
    print("\n🔒 安全配置:")
    print(f"  代码沙箱: {'✅ 已启用' if settings.enable_code_sandbox else '⚠️  未启用（仅测试环境）'}")
    if settings.enable_code_sandbox:
        print(f"  Docker 镜像: {settings.docker_image}")
    
    # 显示错误和警告
    print("\n" + "=" * 60)
    if errors:
        print("❌ 发现错误:")
        for error in errors:
            print(f"  {error}")
        print("\n请检查 .env 文件配置！")
        return False
    
    if warnings:
        print("⚠️  警告:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("✅ 配置检查通过！")
    
    print("=" * 60)
    
    return len(errors) == 0


def test_ai_connection():
    """测试 AI 连接"""
    print("\n🔗 测试 AI 连接...")
    
    try:
        from core.ai_client import ai_client
        
        messages = [
            {"role": "user", "content": "请回复'连接成功'"}
        ]
        
        print("  发送测试消息...")
        response = ai_client.chat(messages, max_tokens=50)
        
        print(f"  ✅ AI 响应: {response}")
        return True
    
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║        智能数据分析工具 - 配置检查工具                   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 检查配置
    config_ok = check_config()
    
    if not config_ok:
        sys.exit(1)
    
    # 询问是否测试 AI 连接
    print("\n是否测试 AI 连接？这会调用 AI API（可能产生费用）")
    response = input("输入 y 测试，其他键跳过: ").lower()
    
    if response == 'y':
        ai_ok = test_ai_connection()
        if not ai_ok:
            sys.exit(1)
    
    print("\n✅ 所有检查通过，可以启动服务了！")
    print("\n运行以下命令启动服务：")
    print("  python main.py")


