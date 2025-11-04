/**
 * 飞书登录页面
 * 处理飞书登录授权，成功后跳转到主页
 */
import { useEffect } from 'react';
import { useFeishuAuth } from '../hooks/useFeishuAuth';
import FeishuLoading from '../components/Feishu/FeishuLoading';
import '../components/Auth/LoginRequired.css';

const Login = () => {
  const { user, loading, login, isFeishuEnv } = useFeishuAuth();

  useEffect(() => {
    // 如果已登录，直接跳转到主页
    if (user) {
      window.location.href = '/';
    }
  }, [user]);

  // ⭐ 移除自动触发登录逻辑，避免刷新后重复授权
  // 用户需要主动点击"点击登录"按钮

  // 加载中
  if (loading) {
    return <FeishuLoading />;
  }

  // 已登录（等待跳转）
  if (user) {
    return <FeishuLoading />;
  }

  // 未登录 - 显示登录页面
  return (
    <div className="login-page">
      {/* 背景装饰 */}
      <div className="login-bg">
        <div className="login-bg-shape shape-1"></div>
        <div className="login-bg-shape shape-2"></div>
        <div className="login-bg-shape shape-3"></div>
      </div>

      {/* 登录卡片 */}
      <div className="login-card">
        {/* Logo 和标题 */}
        <div className="login-header">
          <h1>智能数据分析工具</h1>
          <p className="login-subtitle">让数据分析变得简单高效</p>
        </div>

        {/* 登录内容 */}
        <div className="login-body">
          <div className="login-welcome">
            <h2>欢迎回来</h2>
            <p>使用飞书账号登录，开始你的数据分析之旅</p>
          </div>

          {/* 登录按钮 */}
          <button className="feishu-login-btn" onClick={login}>
            <svg className="feishu-icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 18c-3.31-1.26-6-5.03-6-9V8.3l6-3.07 6 3.07V11c0 3.97-2.69 7.74-6 9z"/>
            </svg>
            <span>使用飞书账号登录</span>
            <svg className="arrow-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M5 12h14M12 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>

          <p className="login-mode-hint">
            {isFeishuEnv ? (
              <><span className="status-dot"></span> 飞书客户端环境</>
            ) : (
              <><span className="status-dot browser"></span> 浏览器网页环境</>
            )}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;

