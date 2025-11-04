"""
飞书网页应用服务端（完整版）
支持多用户登录 + 数据持久化
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
from database import db


# 从 .env 文件加载环境变量
load_dotenv(find_dotenv())

# 获取环境变量
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
FEISHU_HOST = os.getenv("FEISHU_HOST", "https://open.feishu.cn")

# 随机字符串
NONCE_STR = "Y7a8KkqX041bsSwT"

# 创建 Flask 应用
app = Flask(__name__, 
            static_folder='public',
            template_folder='templates')

# 配置
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24小时
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 启用 CORS
CORS(app)

# 初始化鉴权对象
auth = Auth(APP_ID, APP_SECRET, FEISHU_HOST)
user_auth = UserAuth(APP_ID, APP_SECRET, FEISHU_HOST)


@app.route("/")
def index():
    """首页"""
    return send_from_directory('templates', 'index_pro.html')


@app.route("/public/<path:filename>")
def serve_static(filename):
    """静态资源"""
    return send_from_directory('public', filename)


# ============ 用户认证接口 ============

@app.route("/api/login", methods=["POST"])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        code = data.get("code")
        
        if not code:
            return jsonify({"code": -1, "msg": "缺少授权码"}), 400
        
        print(f"收到登录请求，code: {code[:20]}...")
        
        # 获取用户信息
        user_info = user_auth.get_user_info_by_code(code)
        
        # 保存到数据库
        db.save_user(user_info)
        
        # 保存到 session
        session["user_info"] = user_info
        session["login_time"] = time.time()
        session.permanent = True
        
        # 恢复用户的会话上下文
        context = db.get_session_context(session.sid)
        if context:
            session["context"] = context
        
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
        return jsonify({"code": -1, "msg": f"登录失败: {str(e)}"}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    """用户登出"""
    user_info = get_current_user()
    if user_info:
        # 保存会话上下文
        if "context" in session:
            db.save_session_context(
                user_info["open_id"],
                session.sid,
                session["context"]
            )
        print(f"用户登出: {user_info.get('name')}")
    
    session.clear()
    return jsonify({"code": 0, "msg": "登出成功"})


@app.route("/api/current_user", methods=["GET"])
@login_required
def current_user():
    """获取当前用户信息"""
    user_info = get_current_user()
    
    # 获取用户统计信息
    stats = db.get_user_stats(user_info["open_id"])
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {
            "name": user_info.get("name"),
            "avatar_url": user_info.get("avatar_url"),
            "open_id": user_info.get("open_id"),
            "en_name": user_info.get("en_name"),
            "mobile": user_info.get("mobile", ""),
            "email": user_info.get("email", ""),
            "stats": stats
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
            "data": {"logged_in": False}
        })


@app.route("/get_config_parameters", methods=["GET"])
def get_config_parameters():
    """获取 JSSDK 配置参数"""
    try:
        url = request.args.get("url")
        if not url:
            return jsonify({"code": -1, "msg": "缺少 url 参数"}), 400
        
        ticket = auth.get_ticket()
        timestamp = int(time.time()) * 1000
        verify_str = f"jsapi_ticket={ticket}&noncestr={NONCE_STR}&timestamp={timestamp}&url={url}"
        signature = hashlib.sha1(verify_str.encode("utf-8")).hexdigest()
        
        return jsonify({
            "appid": APP_ID,
            "signature": signature,
            "noncestr": NONCE_STR,
            "timestamp": timestamp,
        })
    except Exception as e:
        print(f"获取配置参数失败: {str(e)}")
        return jsonify({"code": -1, "msg": str(e)}), 500


# ============ 数据分析接口（示例） ============

@app.route("/api/analysis/execute", methods=["POST"])
@login_required
def execute_analysis():
    """
    执行数据分析
    将结果保存到数据库，刷新页面后可恢复
    """
    user = get_current_user()
    data = request.get_json()
    
    query = data.get("query")
    file_name = data.get("file_name")
    
    try:
        start_time = time.time()
        
        # 这里调用你的数据分析逻辑
        # result = your_analysis_function(query, file_name)
        
        # 示例结果
        result = {
            "type": "chart",
            "chart_type": "bar",
            "data": [1, 2, 3, 4, 5],
            "labels": ["A", "B", "C", "D", "E"]
        }
        
        execution_time = time.time() - start_time
        
        # 保存到数据库
        analysis_id = db.save_analysis(
            user_id=user["open_id"],
            session_id=session.sid,
            query=query,
            result=result,
            result_type=result.get("type"),
            file_name=file_name,
            chart_type=result.get("chart_type"),
            status="success",
            execution_time=execution_time
        )
        
        return jsonify({
            "code": 0,
            "msg": "分析成功",
            "data": {
                "analysis_id": analysis_id,
                "result": result,
                "execution_time": execution_time
            }
        })
        
    except Exception as e:
        # 保存失败记录
        db.save_analysis(
            user_id=user["open_id"],
            query=query,
            status="error",
            error_message=str(e)
        )
        
        return jsonify({
            "code": -1,
            "msg": f"分析失败: {str(e)}"
        }), 500


@app.route("/api/history", methods=["GET"])
@login_required
def get_history():
    """
    获取用户的分析历史
    刷新页面后可以看到之前的分析记录
    """
    user = get_current_user()
    
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    
    history = db.get_user_history(user["open_id"], limit, offset)
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {
            "history": history,
            "total": len(history)
        }
    })


@app.route("/api/history/<int:analysis_id>", methods=["GET"])
@login_required
def get_analysis_detail(analysis_id):
    """
    获取分析详情
    点击历史记录可以恢复之前的分析结果
    """
    user = get_current_user()
    
    detail = db.get_analysis_detail(analysis_id, user["open_id"])
    
    if detail:
        return jsonify({
            "code": 0,
            "msg": "success",
            "data": detail
        })
    else:
        return jsonify({
            "code": -1,
            "msg": "记录不存在或无权限访问"
        }), 404


@app.route("/api/history/<int:analysis_id>", methods=["DELETE"])
@login_required
def delete_analysis(analysis_id):
    """删除分析记录"""
    user = get_current_user()
    
    success = db.delete_analysis(analysis_id, user["open_id"])
    
    if success:
        return jsonify({"code": 0, "msg": "删除成功"})
    else:
        return jsonify({"code": -1, "msg": "删除失败"}), 404


@app.route("/api/context/save", methods=["POST"])
@login_required
def save_context():
    """
    保存当前页面上下文
    用于保存用户的当前工作状态
    """
    user = get_current_user()
    data = request.get_json()
    
    context_data = data.get("context", {})
    
    # 保存到 session
    session["context"] = context_data
    
    # 保存到数据库
    db.save_session_context(user["open_id"], session.sid, context_data)
    
    return jsonify({"code": 0, "msg": "保存成功"})


@app.route("/api/context/restore", methods=["GET"])
@login_required
def restore_context():
    """
    恢复页面上下文
    刷新页面时自动恢复之前的工作状态
    """
    user = get_current_user()
    
    # 先从 session 获取
    context = session.get("context")
    
    # 如果 session 中没有，从数据库恢复
    if not context:
        context = db.get_session_context(session.sid)
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {"context": context}
    })


@app.route("/api/files", methods=["GET"])
@login_required
def get_user_files():
    """获取用户上传的文件列表"""
    user = get_current_user()
    
    files = db.get_user_files(user["open_id"])
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {"files": files}
    })


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "message": "飞书网页应用服务运行正常（完整版）",
        "features": [
            "多用户登录",
            "数据持久化",
            "会话保持",
            "历史记录"
        ]
    })


def validate_config():
    """验证配置"""
    if not APP_ID or not APP_SECRET:
        raise ValueError("缺少必要的配置信息！请在 .env 文件中配置 APP_ID 和 APP_SECRET")
    
    print("=" * 60)
    print("飞书网页应用配置信息（完整版）：")
    print(f"APP_ID: {APP_ID}")
    print(f"APP_SECRET: {'*' * len(APP_SECRET)}")
    print(f"FEISHU_HOST: {FEISHU_HOST}")
    print(f"数据库: feishu_app.db")
    print(f"功能: 多用户登录 + 数据持久化 + 会话保持")
    print("=" * 60)


if __name__ == "__main__":
    try:
        validate_config()
        
        print("\n🚀 启动飞书网页应用服务（完整版）...")
        print("📝 访问地址: http://127.0.0.1:3000")
        print("👥 支持多用户同时登录")
        print("💾 数据持久化存储")
        print("🔄 刷新页面不丢失状态\n")
        
        app.run(
            host="0.0.0.0",
            port=3000,
            debug=True
        )
        
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        exit(1)

