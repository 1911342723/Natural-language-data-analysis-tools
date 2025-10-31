# Python 3.14 兼容性问题

## ⚠️ 问题

你使用的是 **Python 3.14**，这是一个非常新的版本（2024年10月刚发布）。

**错误信息：**
```
OSError: [WinError 10106] 无法加载或初始化请求的服务提供程序
```

**根本原因：**
- `jupyter-client`、`ipykernel`、`pyzmq` 等包还未完全支持 Python 3.14
- Windows 上的 `_overlapped` 模块加载失败

---

## ✅ 解决方案

### 方案 1：降级到 Python 3.11（推荐）

1. 下载 Python 3.11：https://www.python.org/downloads/release/python-3119/
2. 安装后重新创建虚拟环境：

```bash
# 使用 Python 3.11 创建新环境
py -3.11 -m venv venv

# 激活环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 方案 2：降级到 Python 3.10（更稳定）

```bash
py -3.10 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔍 验证 Python 版本

```bash
python --version
```

**推荐版本：**
- ✅ Python 3.10.x
- ✅ Python 3.11.x
- ⚠️ Python 3.12.x（可能有问题）
- ❌ Python 3.13+ （太新，不推荐）

---

## 为什么不能在代码中修复？

因为：
1. 问题出在 Python 核心库 `_overlapped` 模块
2. 是系统级别的 Winsock 兼容性问题
3. 需要等待 `pyzmq`、`jupyter-client` 等包更新适配 Python 3.14

---

## 快速测试

降级后运行：

```bash
python main.py
```

应该看到：
```
INFO:     Started server process
🚀 启动数据分析工具后端...
✅ 数据库初始化完成
INFO:     Application startup complete.
```

**不再报错**！


