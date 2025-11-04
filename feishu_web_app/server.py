"""
飞书网页应用服务端核心代码
基于 Flask 框架实现
"""
import os
import time
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
from auth import Auth


# 从 .env 文件加载环境变量参数
load_dotenv(find_dotenv())

# 获取环境变量
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
FEISHU_HOST = os.getenv("FEISHU_HOST", "https://open.feishu.cn")

# 随机字符串，用于生成签名
NONCE_STR = "Y7a8KkqX041bsSwT"

# 创建 Flask 应用
app = Flask(__name__, 
            static_folder='public',
            template_folder='templates')

# 启用 CORS（跨域资源共享）
CORS(app)

# 初始化鉴权对象
auth = Auth(APP_ID, APP_SECRET, FEISHU_HOST)


@app.route("/")
def index():
    """
    首页路由，返回 index.html
    """
    return send_from_directory('templates', 'index.html')


@app.route("/public/<path:filename>")
def serve_static(filename):
    """
    静态资源路由，返回 public 目录下的静态文件
    """
    return send_from_directory('public', filename)


@app.route("/get_config_parameters", methods=["GET"])
def get_config_parameters():
    """
    获取并返回前端调用 config 接口所需的参数
    
    前端需要传入参数：
        url: 需要进行鉴权的网页 URL
        
    返回参数：
        appid: 应用 ID
        signature: 签名
        noncestr: 随机字符串
        timestamp: 时间戳
    """
    try:
        # 接入方前端传来的需要鉴权的网页 url
        url = request.args.get("url")
        
        if not url:
            return jsonify({
                "code": -1,
                "msg": "缺少 url 参数"
            }), 400
        
        print(f"收到鉴权请求，URL: {url}")
        
        # 获取 jsapi_ticket
        ticket = auth.get_ticket()
        
        # 当前时间戳，毫秒级
        timestamp = int(time.time()) * 1000
        
        # 拼接成字符串
        # 注意：参数按照字段名的 ASCII 码从小到大排序（字典序）
        verify_str = f"jsapi_ticket={ticket}&noncestr={NONCE_STR}&timestamp={timestamp}&url={url}"
        
        print(f"签名字符串: {verify_str}")
        
        # 对字符串做 sha1 加密，得到签名 signature
        signature = hashlib.sha1(verify_str.encode("utf-8")).hexdigest()
        
        print(f"生成签名: {signature}")
        
        # 将鉴权所需参数返回给前端
        return jsonify({
            "appid": APP_ID,
            "signature": signature,
            "noncestr": NONCE_STR,
            "timestamp": timestamp,
        })
        
    except Exception as e:
        print(f"获取配置参数失败: {str(e)}")
        return jsonify({
            "code": -1,
            "msg": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        "status": "ok",
        "message": "飞书网页应用服务运行正常"
    })


def validate_config():
    """
    验证配置是否正确
    """
    if not APP_ID or not APP_SECRET:
        raise ValueError(
            "缺少必要的配置信息！\n"
            "请在 .env 文件中配置 APP_ID 和 APP_SECRET\n"
            f"当前配置: APP_ID={APP_ID}, APP_SECRET={'*' * len(APP_SECRET) if APP_SECRET else 'None'}"
        )
    
    print("=" * 50)
    print("飞书网页应用配置信息：")
    print(f"APP_ID: {APP_ID}")
    print(f"APP_SECRET: {'*' * len(APP_SECRET)}")
    print(f"FEISHU_HOST: {FEISHU_HOST}")
    print("=" * 50)


if __name__ == "__main__":
    try:
        # 验证配置
        validate_config()
        
        # 启动 Flask 应用
        print("\n🚀 启动飞书网页应用服务...")
        print("📝 访问地址: http://127.0.0.1:3000")
        print("⚠️  请确保在飞书客户端中打开此网页应用\n")
        
        app.run(
            host="0.0.0.0",
            port=3000,
            debug=True
        )
        
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        exit(1)

