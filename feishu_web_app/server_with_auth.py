"""
飞书网页应用服务端（多用户登录版本）
支持多用户同时使用，基于飞书免登授权
"""
import os
import time
import hashlib
import secrets
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
from auth import Auth
from user_auth import UserAuth, login_required, get_current_user


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

# 配置 session（重要：用于多用户支持）
app.config['SECRET_KEY'] = secrets.token_hex(32)  # 随机密钥
app.config['SESSION_TYPE'] = 'filesystem'  # 可以改为 redis
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24小时

# 启用 CORS
CORS(app)

# 初始化鉴权对象
auth = Auth(APP_ID, APP_SECRET, FEISHU_HOST)
user_auth = UserAuth(APP_ID, APP_SECRET, FEISHU_HOST)


@app.route("/")
def index():
    """首页路由"""
    return send_from_directory('templates', 'index_with_auth.html')


@app.route("/public/<path:filename>")
def serve_static(filename):
    """静态资源路由"""
    return send_from_directory('public', filename)


@app.route("/api/login", methods=["POST"])
def login():
    """
    用户登录接口
    前端通过 tt.requestAuthCode 获取 code 后调用此接口
    """
    try:
        data = request.get_json()
        code = data.get("code")
        
        if not code:
            return jsonify({
                "code": -1,
                "msg": "缺少授权码",
                "data": None
            }), 400
        
        print(f"收到登录请求，code: {code[:20]}...")
        
        # 通过 code 获取用户信息
        user_info = user_auth.get_user_info_by_code(code)
        
        # 保存到 session
        session["user_info"] = user_info
        session["login_time"] = time.time()
        session.permanent = True  # 使用持久化 session
        
        print(f"✓ 用户登录成功: {user_info.get('name')} ({user_info.get('open_id')})")
        
        return jsonify({
            "code": 0,
            "msg": "登录成功",
            "data": {
                "name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url"),
                "open_id": user_info.get("open_id"),
                "en_name": user_info.get("en_name"),
                "mobile": user_info.get("mobile", ""),
                "email": user_info.get("email", "")
            }
        })
        
    except Exception as e:
        print(f"✗ 登录失败: {str(e)}")
        return jsonify({
            "code": -1,
            "msg": f"登录失败: {str(e)}",
            "data": None
        }), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    """用户登出接口"""
    user_info = get_current_user()
    if user_info:
        print(f"用户登出: {user_info.get('name')}")
    
    session.clear()
    
    return jsonify({
        "code": 0,
        "msg": "登出成功",
        "data": None
    })


@app.route("/api/current_user", methods=["GET"])
@login_required
def current_user():
    """
    获取当前登录用户信息
    需要登录才能访问
    """
    user_info = get_current_user()
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {
            "name": user_info.get("name"),
            "avatar_url": user_info.get("avatar_url"),
            "open_id": user_info.get("open_id"),
            "en_name": user_info.get("en_name"),
            "mobile": user_info.get("mobile", ""),
            "email": user_info.get("email", "")
        }
    })


@app.route("/api/check_login", methods=["GET"])
def check_login():
    """检查登录状态"""
    user_info = get_current_user()
    
    if user_info:
        return jsonify({
            "code": 0,
            "msg": "已登录",
            "data": {
                "logged_in": True,
                "name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url")
            }
        })
    else:
        return jsonify({
            "code": 0,
            "msg": "未登录",
            "data": {
                "logged_in": False
            }
        })


@app.route("/get_config_parameters", methods=["GET"])
def get_config_parameters():
    """
    获取 JSSDK 配置参数
    用于前端 JSAPI 鉴权
    """
    try:
        url = request.args.get("url")
        
        if not url:
            return jsonify({
                "code": -1,
                "msg": "缺少 url 参数"
            }), 400
        
        print(f"收到鉴权请求，URL: {url}")
        
        ticket = auth.get_ticket()
        timestamp = int(time.time()) * 1000
        
        verify_str = f"jsapi_ticket={ticket}&noncestr={NONCE_STR}&timestamp={timestamp}&url={url}"
        signature = hashlib.sha1(verify_str.encode("utf-8")).hexdigest()
        
        print(f"生成签名: {signature}")
        
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


# ============ 业务接口示例（需要登录） ============

@app.route("/api/data/analysis", methods=["POST"])
@login_required
def data_analysis():
    """
    数据分析接口示例
    只有登录用户才能访问
    """
    user_info = get_current_user()
    
    # 这里实现你的数据分析逻辑
    # 可以根据 user_info 区分不同用户的数据
    
    return jsonify({
        "code": 0,
        "msg": "分析成功",
        "data": {
            "user": user_info.get("name"),
            "result": "这里是分析结果"
        }
    })


@app.route("/api/user/history", methods=["GET"])
@login_required
def user_history():
    """
    获取用户历史记录
    每个用户只能看到自己的历史
    """
    user_info = get_current_user()
    open_id = user_info.get("open_id")
    
    # 根据 open_id 查询该用户的历史记录
    # history = query_user_history(open_id)
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {
            "user": user_info.get("name"),
            "history": []  # 这里返回该用户的历史记录
        }
    })


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "message": "飞书网页应用服务运行正常（多用户版）"
    })


def validate_config():
    """验证配置"""
    if not APP_ID or not APP_SECRET:
        raise ValueError(
            "缺少必要的配置信息！\n"
            "请在 .env 文件中配置 APP_ID 和 APP_SECRET\n"
            f"当前配置: APP_ID={APP_ID}, APP_SECRET={'*' * len(APP_SECRET) if APP_SECRET else 'None'}"
        )
    
    print("=" * 50)
    print("飞书网页应用配置信息（多用户版）：")
    print(f"APP_ID: {APP_ID}")
    print(f"APP_SECRET: {'*' * len(APP_SECRET)}")
    print(f"FEISHU_HOST: {FEISHU_HOST}")
    print(f"SESSION_KEY: {app.config['SECRET_KEY'][:20]}...")
    print("=" * 50)


if __name__ == "__main__":
    try:
        validate_config()
        
        print("\n🚀 启动飞书网页应用服务（多用户版）...")
        print("📝 访问地址: http://127.0.0.1:3000")
        print("👥 支持多用户同时登录")
        print("🔐 基于飞书免登授权\n")
        
        app.run(
            host="0.0.0.0",
            port=3000,
            debug=True
        )
        
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        exit(1)

