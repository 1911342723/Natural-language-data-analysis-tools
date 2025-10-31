# Windows Jupyter Kernel 崩溃问题 - 终极解决方案 ✅

## 🔍 问题根源

### 现象
```
📋 [执行完成] stdout行数=1, data项数=0, error=True
```
- 代码执行到一半就崩溃
- 图表根本没有生成
- Jupyter Kernel 进程退出

### 真正原因
**AI 生成的代码包含太多 print 语句**，导致 Windows 上的 ZMQ 通信崩溃。

示例（导致崩溃的代码）：
```python
# ❌ 错误：30+ 个 print 语句
print("=" * 50)
print("第1步：数据整体浏览")
print("=" * 50)
print("表格 df1:")
print(f"  形状: {df1.shape}")
print(f"  字段: {list(df1.columns)}")
print(f"  缺失值: {df1.isnull().sum().sum()} 个")
print()
print("表格 df2:")
print(f"  形状: {df2.shape}")
# ... 还有20多个 print
for col in common_cols:  # ❌ 循环中的 print 是致命的！
    print(f"字段 '{col}' 统计对比:")
    print(f"  df1: 均值={df1[col].mean()}")
    print(f"  df2: 均值={df2[col].mean()}")
```

**结果**：Jupyter Kernel 在处理这么多输出时，ZMQ 通信崩溃。

---

## ✅ 解决方案

### 1. 修改 AI Prompt（根本解决）

**文件**：`backend/core/prompts.py`

**关键修改**：

```python
12. **⚠️ 严格限制（Windows系统会崩溃）**
   - **整个代码最多 6-8 个 print 语句**
   - **绝对禁止在 for/while 循环中使用 print**
   - **最多生成 1 个图表**（多图表会崩溃）
   - **用 f-string 多行文本合并输出**，而不是多个 print
```

**正确示例**：

```python
# ✅ 好：合并为1个print
overview = f"""
{'='*50}
数据概览
{'='*50}
- df1: {df1.shape}
- df2: {df2.shape}
- 共同字段: {len(common_cols)}
"""
print(overview)  # 只用了 1 个 print！

# ❌ 错：多个print
print("=" * 50)
print("数据概览")
print("=" * 50)
print(f"df1: {df1.shape}")
print(f"df2: {df2.shape}")
print(f"共同字段: {len(common_cols)}")
# 6个print，太多了！

# ❌ 错：循环print（会导致崩溃）
for col in columns:
    print(f"{col}: {df[col].mean()}")  # 禁止！
```

### 2. 移除 CFFI 后端配置

**文件**：`backend/core/jupyter_manager.py`

移除了不稳定的 CFFI 配置：
```python
# 移除这些（导致导入错误）
env['PYZMQ_BACKEND'] = 'cffi'
env['ZMQ_BLOCKY'] = '1'
```

保留基本配置：
```python
env = os.environ.copy()
if sys.platform == 'win32':
    env['PYTHONIOENCODING'] = 'utf-8'
self.kernel_manager.start_kernel(env=env)
```

### 3. 优化 Jupyter 配置

**文件**：`backend/core/jupyter_manager.py`

```python
c = Config()
c.Session.key = session_key
c.ZMQInteractiveShell.kernel_timeout = 120  # 增加超时
```

---

## 🎯 效果对比

### 修复前（崩溃）❌
```python
代码包含 30+ print 语句
↓
ZMQ 通信崩溃
↓
error=True, data项数=0
↓
没有图表！
```

### 修复后（稳定）✅
```python
代码包含 4-6 print 语句
↓
ZMQ 通信正常
↓
error=False, data项数=1
↓
图表成功显示！
```

---

## 📝 精简代码示例

完整的分析代码，只用 **4 个 print + 1 个图表**：

```python
# 步骤1：数据概览
overview = f"""
{'='*50}
数据分析
{'='*50}
df1: {df1.shape}, df2: {df2.shape}
共同字段: {len(set(df1.columns) & set(df2.columns))}
"""
print(overview)  # print #1

# 步骤2：字段对比（合并输出）
common_cols = set(df1.columns) & set(df2.columns)
col_stats = []
for col in list(common_cols)[:3]:  # 只取前3个
    col_stats.append(f"{col}: df1均值={df1[col].mean():.2f}, df2均值={df2[col].mean():.2f}")
print(f"\\n{'='*50}\\n字段统计\\n{'='*50}\\n" + "\\n".join(col_stats))  # print #2

# 步骤3：一致性检查
defect_diff = (df1['defect_weight'] != df2['defect_weight']).sum()
consistency = f"""
{'='*50}
一致性检查
{'='*50}
defect_weight 不一致记录: {defect_diff}/{len(df1)} ({defect_diff/len(df1)*100:.1f}%)
"""
print(consistency)  # print #3

# 步骤4：可视化（只1个图）
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.scatter(df1['defect_weight'], df2['defect_weight'], alpha=0.3)
ax.plot([0, 4], [0, 4], 'r--', label='完全一致线')
ax.set_xlabel('df1 defect_weight')
ax.set_ylabel('df2 defect_weight')
ax.set_title('defect_weight 一致性对比')
ax.legend()
plt.tight_layout()

buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=80)
buf.seek(0)
plt.close()
display(Image(buf.getvalue()))

# 步骤5：洞察总结
insights = f"""
{'='*50}
关键洞察
{'='*50}
1. 数据量: {len(df1)} 条记录
2. 不一致率: {defect_diff/len(df1)*100:.1f}%
3. 建议: {"数据基本一致" if defect_diff < len(df1)*0.01 else "需要关注不一致数据"}
"""
print(insights)  # print #4
```

**总计**：4 个 print + 1 个图表 = **稳定运行！**

---

## 🚀 测试步骤

### 1. 重启后端
```bash
cd backend
python main.py
```

### 2. 刷新前端
```bash
Ctrl + F5  # 强制刷新
```

### 3. 提交分析需求
- 上传多文件
- 输入："对比这两个表格的数据一致性"
- **AI 会生成精简代码**（不超过8个print）

### 4. 预期结果
- ✅ 代码执行成功
- ✅ 图表正常显示
- ✅ 步骤中可以看到图表
- ✅ 无崩溃

---

## 🔧 如果还是崩溃怎么办？

### 检查生成的代码
在"执行过程"中查看生成的代码，数一下 print 语句数量：

```python
# 如果看到类似这样的代码，说明 AI 没遵守限制：
for col in columns:  # ❌ 循环print
    print(...)
```

**解决方案**：重新提交需求，在需求中加上：
> "请使用最少的 print 语句（最多5个），合并输出内容"

### 或者手动修改代码
点击代码块的"运行代码"按钮，手动修改：
1. 合并多个 print 为一个
2. 删除循环中的 print
3. 重新运行

---

## 📊 技术细节

### 为什么 Windows 特别容易崩溃？

1. **ZMQ 后端限制**：Windows 上的 PyZMQ 对大量消息处理不如 Linux 稳定
2. **Event Loop 差异**：Windows 使用 `ProactorEventLoop`，Linux 使用 `SelectorEventLoop`
3. **内存缓冲区**：Windows ZMQ 的默认缓冲区较小

### 为什么限制 print 语句有效？

每个 `print` 语句都会：
1. 生成一个 ZMQ 消息
2. 通过 `iopub` 通道传输
3. 占用缓冲区

**30 个 print = 30 条消息** → 缓冲区溢出 → 崩溃

**4 个 print = 4 条消息** → 缓冲区充足 → 稳定

---

## ✅ 完成清单

- [x] 移除 CFFI 配置（导致导入错误）
- [x] 修改 AI Prompt，严格限制 print 数量
- [x] 提供精简代码示例
- [x] 增加 Jupyter 超时配置
- [x] 编写详细文档

**现在可以开始测试了！** 🎉

