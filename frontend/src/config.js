/**
 * 前端配置文件
 */

// API 基础地址
// 生产模式使用相对路径（避免跨域），开发模式使用绝对路径
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// 飞书配置
export const FEISHU_CONFIG = {
  APP_ID: 'cli_a847b85cdf7dd00c',  // 你的飞书 APP_ID
  // 注意：APP_SECRET 不能放在前端！
};

// 是否启用飞书登录（开发时可以关闭）
export const ENABLE_FEISHU_AUTH = import.meta.env.VITE_ENABLE_FEISHU_AUTH !== 'false';

