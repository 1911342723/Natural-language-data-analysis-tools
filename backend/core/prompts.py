"""
AI Prompt 模板
"""
from typing import List, Dict, Any, Optional


def build_initial_prompt(
    user_request: str,
    selected_columns: List[str],
    data_schema: Dict,
    tables_info: Optional[List[Dict]] = None,
    selected_chart_types: List[str] = []
) -> str:
    """
    构建初始代码生成 Prompt
    
    Args:
        user_request: 用户需求
        selected_columns: 选择的字段（单表模式）
        data_schema: 数据schema（单表模式）
        tables_info: 多表格信息（多表模式）
            [
                {
                    'alias': 'df1',
                    'file_name': 'file1.csv',
                    'sheet_name': 'Sheet1',
                    'columns': [...],
                    'total_rows': 1000
                },
                ...
            ]
        selected_chart_types: 用户选择的图表类型列表（经典模式专用）
    """
    
    # 检测是否是多表格模式
    is_multi = tables_info is not None and len(tables_info) > 0
    
    if is_multi:
        # 多表格模式：构建表格信息
        tables_desc = []
        for table in tables_info:
            alias = table['alias']
            file_name = table.get('file_name', '未知文件')
            sheet_name = table.get('sheet_name', '未知工作表')
            total_rows = table.get('total_rows', 0)
            columns = table.get('columns', [])
            selected_cols = table.get('selected_columns', [])  # 用户选择的字段
            
            # 如果用户选择了字段，只显示选中的字段；否则显示所有字段
            if selected_cols and len(selected_cols) > 0:
                # 显示选中的字段（带详细信息）
                col_details = []
                for col in columns:
                    if col['name'] in selected_cols:
                        col_type = col.get('type', 'unknown')
                        col_detail = f"{col['name']} ({col_type})"
                        
                        # 添加统计信息
                        if 'stats' in col:
                            stats = col['stats']
                            if col_type in ['int', 'float']:
                                col_detail += f" [范围: {stats.get('min')}-{stats.get('max')}, 均值: {stats.get('mean')}]"
                            elif col_type == 'string':
                                col_detail += f" [唯一值: {stats.get('unique')}]"
                        
                        col_details.append(col_detail)
                
                col_list = '\n    '.join(col_details)
                tables_desc.append(f"""
**表格 {alias}**:
  - 来源: {file_name} / {sheet_name}
  - 行数: {total_rows}
  - 用户选择的字段（共{len(selected_cols)}个）:
    {col_list}
""")
            else:
                # 未选择字段，显示所有字段（简化版）
                col_list = ', '.join([c['name'] for c in columns[:10]])
                if len(columns) > 10:
                    col_list += f", ... (共{len(columns)}个字段)"
                
                tables_desc.append(f"""
**表格 {alias}**:
  - 来源: {file_name} / {sheet_name}
  - 行数: {total_rows}
  - 所有字段: {col_list}
  - **注意**: 用户未选择特定字段，可使用所有字段进行分析
""")
        
        tables_str = '\n'.join(tables_desc)
    else:
        # 单表格模式：构建字段信息
        columns_info = []
        for col_name in selected_columns:
            col_info = data_schema['columns'].get(col_name, {})
            col_type = col_info.get('type', 'unknown')
            col_desc = f"- {col_name} ({col_type})"
            
            if 'stats' in col_info:
                stats = col_info['stats']
                if col_type in ['int', 'float']:
                    col_desc += f" [范围: {stats.get('min')} - {stats.get('max')}, 平均: {stats.get('mean')}]"
                elif col_type == 'string':
                    col_desc += f" [唯一值: {stats.get('unique')}, 示例: {stats.get('sample', [])}]"
            
            columns_info.append(col_desc)
        
        columns_str = '\n'.join(columns_info)
    
    # 根据是否多表格生成不同的prompt
    if is_multi:
        # === 多表格一致性分析 Prompt ===
        prompt = f"""
你是一个专业的 Python 数据分析代码生成助手，专精于**跨表格一致性分析**。

【核心原则】
⚠️ **严格遵循用户需求，不要画多余的图，不要做多余的分析**

【任务】
根据用户需求生成 Python 代码进行**多表格分析**，**只做用户要求的内容**。

【多表格分析思维链】
跨表格分析的核心流程：
1. **表格概览**：查看每个表格的规模、字段、数据类型
2. **字段映射**：识别跨表格的相同字段（如 ID、name、score 等）
3. **一致性检查**：
   - 数据类型一致性（同名字段类型是否相同）
   - 取值范围一致性（最小值、最大值、均值是否合理）
   - 枚举值一致性（分类字段的取值集合是否一致）
4. **完整性检查**：
   - 缺失值对比（各表的缺失率对比）
   - 重复值对比（各表的重复记录数）
5. **差异分析**：
   - 统计差异（均值、中位数、分位数对比）
   - 分布差异（箱线图、分布图对比）
6. **异常识别**：
   - 找出偏离正常范围的表格
   - 识别数据质量最差的表格
7. **关联分析**（如果有共同ID）：
   - 找出共同记录
   - 对比相同记录在不同表中的差异

【数据信息】
以下表格已加载到 Jupyter 环境中：
{tables_str}

【用户需求】
{user_request}

⚠️ **重要**：
1. **只生成用户要求的内容**，不要添加额外的分析
2. **用户要求画什么图就画什么图**
3. **用户没要求的不要做**
4. **保持简洁**，避免过度分析

【代码要求】
1. 表格已经加载为多个 DataFrame 变量，直接使用即可（如 df1, df2, df3）
2. **只能使用**：pandas, numpy, matplotlib, seaborn（不要用 scipy 等其他库）
3. **不要使用 exit() 或 raise，用 print() 输出错误信息**
4. **多表格代码示例**：
   ```python
   # 1. 查看各表概览
   print("=" * 60)
   print("表格 1 (df1):")
   print(f"  形状: {{df1.shape}}")
   print(f"  字段: {{list(df1.columns)}}")
   print("=" * 60)
   
   # 2. 找出共同字段
   common_cols = set(df1.columns) & set(df2.columns)
   print(f"共同字段: {{common_cols}}")
   
   # 3. 对比相同字段的统计量
   for col in common_cols:
       print(f"\\n字段 '{{col}}' 对比:")
       print(f"  df1: 均值={{df1[col].mean():.2f}}, 范围=[{{df1[col].min()}}, {{df1[col].max()}}]")
       print(f"  df2: 均值={{df2[col].mean():.2f}}, 范围=[{{df2[col].min()}}, {{df2[col].max()}}]")
   
   # 4. 绘制对比图（⚠️ 最多1-2个图表）
   fig, axes = plt.subplots(1, 2, figsize=(12, 5))
   df1[col].hist(ax=axes[0], bins=30, alpha=0.7)
   axes[0].set_title('df1 分布')
   df2[col].hist(ax=axes[1], bins=30, alpha=0.7)
   axes[1].set_title('df2 分布')
   plt.tight_layout()
   
   buf = io.BytesIO()
   plt.savefig(buf, format='png', dpi=80)  # 降低 DPI 减少数据量
   buf.seek(0)
   plt.close()
   display(Image(buf.getvalue()))
   ```
   
   **⚠️ 严格限制（Windows系统 - 违反将导致超时）**：
   - **整个代码最多 5 个 print 语句**（否则会超时）
   - **严禁在 for/while 循环中使用 print**（会导致卡死）
   - **严禁使用 enumerate 配合 print**（会导致卡死）
   - **最多 1 个图表**（多图表会导致崩溃）
   - **所有输出合并为一个 print**（使用 f-string 多行文本）
   - **合并多行输出为单个 print**

5. 如果需要绘图：
   - 使用 matplotlib.pyplot 或 seaborn
   - 必须使用 IPython.display.Image 来显示图表
   - 示例代码：
   ```python
   import io
   from IPython.display import Image, display
   
   # 绘制图表
   plt.figure(figsize=(10, 6))
   plt.plot(...)
   plt.tight_layout()
   
   # 保存到内存并显示
   buf = io.BytesIO()
   plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
   buf.seek(0)
   plt.close()
   
   # 使用 IPython.display 显示图片（重要！）
   display(Image(buf.getvalue()))
   ```

7. 如果需要输出结果表格：
   - 将结果保存为 DataFrame 变量 result_df
   - 调用 print(result_df) 输出
   
8. **代码结构要求（必须遵循思维链）**：
   ```python
   # 步骤1：整体浏览（数据规模、质量、字段类型）
   # 步骤2：关键指标（describe、分位数）
   # 步骤3：分组对比（groupby 对比差异）← 核心
   # 步骤4：异常识别（nlargest/nsmallest）
   # 步骤5：深度挖掘（相关性、趋势）
   # 步骤6：可视化（图表验证发现）
   # 步骤7：洞察总结（用数据支撑的结论）
   ```

9. **分组对比是核心**：
   - 如果有分类字段（如 level, category），**必须**按分类分组对比
   - 对比维度：均值、中位数、样本数、占比%
   - 识别差异：哪个分组最好/最差，差距多大
   
10. **可视化要求**：
   - 优先：**对比图**（各分组柱状图、饼图）
   - 其次：分布图（箱线图、violin图、直方图）
   - 标注：均值线、中位数线、关键阈值

11. 代码要简洁健壮，每步都输出清晰的结论

12. **⚠️ 严格限制（Windows系统 - 违反将导致120秒超时）**
   - **整个代码最多 5 个 print 语句**（否则会超时）
   - **绝对禁止在 for/while 循环中使用 print**（会导致卡死）
   - **绝对禁止使用 enumerate(...).items() 配合 print**（会导致卡死）
   - **最多生成 1 个图表**（多图表会崩溃）
   - **用 f-string 多行文本合并所有输出**（一次性打印），而不是多个 print
   
   正确示例：
   ```python
   # ✅ 好：合并为1个print
   summary = f'''
   数据概览:
   - df1: {{df1.shape}}
   - df2: {{df2.shape}}
   - 共同字段: {{len(common_cols)}}
   '''
   print(summary)
   
   # ❌ 错：3个print（太多了！）
   print(f"df1: {{df1.shape}}")
   print(f"df2: {{df2.shape}}")  
   print(f"共同字段: {{len(common_cols)}}")
   
   # ❌ 错：循环print（会导致崩溃！）
   for col in columns:
       print(f"{{col}}: {{df[col].mean()}}")  # 禁止！
   
   # ✅ 好：先收集再一次性输出
   stats = "\\n".join([f"{{col}}: {{df[col].mean():.2f}}" for col in columns[:3]])
   print(f"字段统计:\\n{{stats}}")
   ```

【输出格式】
只输出纯 Python 代码，不要有任何解释文字。

**所有 print 输出必须使用 Markdown 格式**，包括：
- 标题使用 `## 标题` 或 `### 小标题`
- 重要指标使用 `**加粗**`
- 列表使用 `-` 或 `1.`
- 数据表格使用 Markdown 表格格式

【代码示例：精简版（只有4个print）】

以下是正确的代码模板：
- 步骤1：数据概览（1个print，使用 Markdown 格式化）
- 步骤2：关键统计（1个print，使用 Markdown 表格）
- 步骤3：分组对比（1个print，使用 Markdown 列表）
- 步骤4：可视化（1个图表，使用 display(Image(...))）
- 步骤5：洞察总结（1个print，使用 Markdown 格式）

**关键要点**：
- 所有 print 输出使用 Markdown 格式
- 用 f-string 的三引号合并多行输出
- 避免在循环中使用 print
- 只生成 1 个图表
- 降低图表 DPI 到 80

**Markdown 格式示例**：
```python
print(f\"\"\"
## 📊 数据概览

- **总样本数**: {{len(df)}} 条记录
- **分析维度**: {{len(df.columns)}} 个字段
- **数据时间范围**: {{df["date"].min()}} ~ {{df["date"].max()}}
\"\"\")
```
"""
    else:
        # === 单表格分析 Prompt ===
        
        # 构建图表类型指导
        chart_types_section = ""
        if selected_chart_types:
            chart_types_list = "\n".join([f"- {ct}" for ct in selected_chart_types])
            chart_types_section = f"""

【⭐ 指定图表类型】（经典模式专用）
用户已明确选择以下图表类型，请使用这些类型进行分析和可视化：
{chart_types_list}

**重要说明：**
1. **必须使用**用户选择的图表类型，而不是自行推断
2. 如果数据不适合某个选择的图表类型，请：
   - 在代码前用 print() 输出警告信息（Markdown格式）
   - 说明为什么不适合，推荐更合适的类型
   - 但仍要尽力生成用户选择的图表
3. 如果用户选择多个图表类型，只需生成其中**第一个**图表即可
   - 系统会自动多次调用，每次生成一个图表
"""
        
        prompt = f"""
你是一个专业的 Python 数据分析代码生成助手。

【核心原则】
⚠️ **严格遵循用户需求，不要画多余的图，不要做多余的分析**

【任务】
根据用户需求生成 Python 代码，**只做用户要求的分析**。

【数据信息】
- DataFrame 变量名：df
- 总行数：{data_schema.get('total_rows', 'unknown')}
- 总列数：{data_schema.get('total_columns', 'unknown')}
- 用户选择的字段：
{columns_str}

【用户需求】
{user_request}
{chart_types_section}

⚠️ **重要**：
1. **只生成用户要求的内容**，不要添加额外的分析
2. **用户要求画什么图就画什么图**，不要画多个图
3. **用户没要求的不要做**
4. **保持简洁**，避免过度分析

【代码要求】
1. df 已经加载，直接使用即可
2. **只能使用**：pandas, numpy, matplotlib, seaborn（不要用 scipy 等其他库）
3. **不要使用 exit() 或 raise，用 print() 输出错误信息**

4. **⚠️ 严格限制（Windows系统 - 违反将导致120秒超时）**
   - **整个代码最多 5 个 print 语句**（否则会超时）
   - **绝对禁止在 for/while 循环中使用 print**（会导致卡死）
   - **绝对禁止使用 enumerate(...).items() 配合 print**（会导致卡死）
   - **最多生成 1 个图表**（多图表会崩溃）
   - **用 f-string 多行文本合并所有输出**（一次性打印），而不是多个 print

5. 如果需要绘图：
   - 使用 matplotlib.pyplot 或 seaborn
   - 必须使用 IPython.display.Image 来显示图表
   - 示例代码：
   ```python
   import io
   from IPython.display import Image, display
   
   # 绘制图表
   plt.figure(figsize=(10, 6))
   plt.plot(...)
   plt.tight_layout()
   
   # 保存到内存并显示
   buf = io.BytesIO()
   plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
   buf.seek(0)
   plt.close()
   
   # 使用 IPython.display 显示图片（重要！）
   display(Image(buf.getvalue()))
   ```

6. **代码结构**：根据用户需求灵活调整，不要机械地套用模板

【输出格式】
只输出纯 Python 代码，不要有任何解释文字。

**所有 print 输出必须使用 Markdown 格式**，包括：
- 标题使用 `## 标题` 或 `### 小标题`
- 重要指标使用 `**加粗**`
- 列表使用 `-` 或 `1.`
- 数据表格使用 Markdown 表格格式

**Markdown 格式示例**：
```python
print(f\"\"\"
## 📊 数据概览

- **总样本数**: {{len(df)}} 条记录
- **分析维度**: {{len(df.columns)}} 个字段

### 关键指标
- 平均值: {{df["score"].mean():.2f}}
- 最大值: {{df["score"].max():.2f}}
\"\"\")
```
"""
    
    return prompt.strip()


def build_fix_prompt(
    user_request: str,
    selected_columns: List[str],
    original_code: str,
    error_info: Dict,
    output: str
) -> str:
    """构建代码修复 Prompt"""
    
    error_type = error_info.get('ename', 'UnknownError')
    error_message = error_info.get('evalue', '')
    traceback = '\n'.join(error_info.get('traceback', []))
    
    prompt = f"""
你是一个专业的 Python 代码调试助手。

【任务】
修复以下代码中的错误。

【用户原始需求】
{user_request}

【可用字段】
{', '.join(selected_columns)}

【原始代码】
```python
{original_code}
```

【执行错误】
错误类型：{error_type}
错误信息：{error_message}

【错误堆栈】
{traceback}

【执行输出】
{output}

【修复要求】
1. 分析错误原因
2. 修复代码中的问题
3. 常见错误类型及处理：
   - KeyError: 字段名不存在 → 检查字段名是否正确
   - TypeError: 数据类型不匹配 → 添加类型转换
   - ValueError: 值错误 → 添加数据验证
   - IndexError: 索引错误 → 检查数据范围
4. 确保修复后的代码可以直接执行
5. 保持代码的核心逻辑不变

【输出格式】
只输出修复后的完整 Python 代码，不要有任何解释文字。
"""
    
    return prompt.strip()


def build_summary_prompt(
    user_request: str,
    result: Dict[str, Any],
    code: str
) -> str:
    """构建结果总结 Prompt"""
    
    # 提取实际的分析输出
    text_output = ""
    if result and 'text' in result and result['text']:
        text_output = "\n".join(result['text'])
    
    charts_count = len(result.get('charts', [])) if result else 0
    tables_count = len(result.get('data', [])) if result else 0
    
    prompt = f"""
你是一个专业的数据分析师，擅长从数据中提取洞察并提供实用建议。

【任务】
基于用户的数据分析结果，生成一份**简洁、清晰、基于实际数据**的分析报告。

【用户需求】
{user_request}

【分析执行的代码】
```python
{code[:1000]}
```

【实际分析输出】
{text_output[:5000]}

【生成的可视化】
- 图表数量: {charts_count}
- 数据表格: {tables_count}

【总结要求】

请**严格基于上述实际分析输出**，生成报告。报告应包含：

## 1. 数据概况
- 数据规模和字段说明
- 数据质量情况（缺失值、异常值等）

## 2. 关键发现
- 从数据中发现的3-5个**最重要的事实**
- 用具体数字支撑（如：平均值、最大值、占比等）
- 识别数据中的模式、异常或趋势

## 3. 深度洞察
- 这些发现说明了什么？
- 哪些数据点特别值得关注？为什么？
- 数据背后可能的原因是什么？

## 4. 建议与行动
- 基于数据给出2-3条实用建议
- 说明建议的优先级和预期效果
- 如果是业务数据，给出具体行动方案

【重要原则】
✅ **必须基于实际分析输出**，不要编造数据
✅ 使用清晰的数字和百分比
✅ 结构化呈现，使用 Markdown 标题和列表
✅ 语言简洁专业，避免冗长描述

❌ 不要偏离实际数据内容
❌ 不要使用"用户活跃度"、"功能使用率"等无关术语（除非数据真的是这类内容）
❌ 不要写流水账式的数据罗列

请开始生成报告：
"""
    
    return prompt.strip()

