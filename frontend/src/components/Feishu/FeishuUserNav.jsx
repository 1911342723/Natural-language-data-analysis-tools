/**
 * 飞书用户导航栏组件
 * 显示用户头像、姓名和下拉菜单
 */
import { useState, useRef, useEffect } from 'react';
import './FeishuUserNav.css';

const FeishuUserNav = ({ user, onLogout }) => {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) return null;

  return (
    <div className="feishu-user-nav" ref={menuRef}>
      {/* 用户信息按钮 */}
      <div 
        className="user-dropdown-trigger"
        onClick={() => setShowMenu(!showMenu)}
      >
        <img 
          src={user.avatar_url} 
          alt={user.name} 
          className="user-avatar-small" 
        />
        <span className="user-name">{user.name}</span>
        <svg 
          className={`dropdown-icon ${showMenu ? 'open' : ''}`}
          width="12" 
          height="12" 
          viewBox="0 0 12 12" 
          fill="currentColor"
        >
          <path d="M6 8L2 4h8L6 8z"/>
        </svg>
      </div>

      {/* 下拉菜单 */}
      {showMenu && (
        <div className="user-dropdown-menu">
          {/* 用户信息头部 */}
          <div className="menu-header">
            <img 
              src={user.avatar_url} 
              alt={user.name} 
              className="user-avatar-large" 
            />
            <div className="user-info">
              <div className="user-name-large">{user.name}</div>
              {user.email && (
                <div className="user-email">{user.email}</div>
              )}
            </div>
          </div>

          <div className="menu-divider"></div>

          {/* 菜单项 */}
          <div className="menu-items">
            {user.stats && (
              <div className="menu-stats">
                <div className="stat-item">
                  <span className="stat-label">总分析</span>
                  <span className="stat-value">{user.stats.total_analysis || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">成功率</span>
                  <span className="stat-value">{user.stats.success_rate || 0}%</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">上传文件</span>
                  <span className="stat-value">{user.stats.file_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">活跃天数</span>
                  <span className="stat-value">{user.stats.active_days || 0}</span>
                </div>
              </div>
            )}
          </div>

          <div className="menu-divider"></div>

          {/* 退出登录 */}
          <button 
            className="menu-item logout-btn"
            onClick={() => {
              setShowMenu(false);
              onLogout();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M11 5l3 3-3 3M14 8H6"/>
            </svg>
            退出登录
          </button>
        </div>
      )}
    </div>
  );
};

export default FeishuUserNav;

