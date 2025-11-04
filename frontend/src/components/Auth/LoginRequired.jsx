/**
 * 登录保护组件
 * 未登录时显示登录提示，已登录时显示子组件
 */
import { useFeishuAuth } from '@/hooks/useFeishuAuth';
import FeishuLoading from '../Feishu/FeishuLoading';
import './LoginRequired.css';

const LoginRequired = ({ children }) => {
  const { user, loading, login, isFeishuEnv } = useFeishuAuth();

  // 加载中
  if (loading) {
    return <FeishuLoading />;
  }

  // 未登录
  if (!user) {
    return (
      <div className="login-required-container">
        <div className="login-required-content">
          <div className="lock-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" strokeWidth="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4" strokeWidth="2"/>
            </svg>
          </div>
          
          <h2>需要登录</h2>
          <p className="login-hint">
            {isFeishuEnv 
              ? '请先登录飞书账号才能使用数据分析功能' 
              : '请在飞书客户端中打开此应用'}
          </p>
          
          {isFeishuEnv ? (
            <button className="login-action-btn" onClick={login}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
              </svg>
              立即登录
            </button>
          ) : (
            <div className="qr-code-hint">
              <p>扫描二维码在飞书中打开：</p>
              <div className="qr-placeholder">
                <svg width="100" height="100" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z"/>
                </svg>
              </div>
              <p className="small-hint">或直接在飞书客户端中打开应用</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 已登录，显示子组件
  return <>{children}</>;
};

export default LoginRequired;

