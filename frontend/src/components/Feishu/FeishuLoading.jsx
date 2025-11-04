/**
 * 飞书登录加载组件
 * 显示登录加载状态
 */
import './FeishuLoading.css';

const FeishuLoading = () => {
  return (
    <div className="feishu-loading-overlay">
      <div className="feishu-loading-content">
        <div className="loading-spinner"></div>
        <p className="loading-text">正在登录飞书...</p>
        <p className="loading-hint">请稍候</p>
      </div>
    </div>
  );
};

export default FeishuLoading;


