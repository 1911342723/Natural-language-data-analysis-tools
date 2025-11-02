"""
科研级图表生成专用 Prompt 模板
"""
from typing import List, Dict, Any


# 科研图表配置字典
RESEARCH_CHART_CONFIGS = {
    "publication": {
        "name": "出版级（Publication）",
        "description": "符合Nature/Science等期刊投稿标准",
        "config": {
            "dpi": 300,
            "font_family": "Arial",
            "font_size": 10,
            "figure_size": (3.5, 2.5),  # 单栏尺寸（英寸）
            "colors": ["#000000", "#666666", "#999999", "#CCCCCC"],  # 黑白灰友好
            "line_width": 1.5,
            "grid": False,
            "spine_visible": ["left", "bottom"],
        }
    },
    "presentation": {
        "name": "演示风格（Presentation）",
        "description": "适合会议展示和PPT",
        "config": {
            "dpi": 150,
            "font_family": "Arial",
            "font_size": 14,
            "figure_size": (10, 6),
            "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "line_width": 2.5,
            "grid": True,
            "spine_visible": ["left", "bottom", "right", "top"],
        }
    },
    "web": {
        "name": "Web风格",
        "description": "适合网页展示，使用交互式图表",
        "config": {
            "dpi": 100,
            "font_family": "sans-serif",
            "font_size": 12,
            "figure_size": (12, 7),
            "colors": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"],
            "interactive": True,
            "use_plotly": True,
        }
    }
}


def build_research_chart_prompt(
    user_request: str,
    selected_columns: List[str],
    data_schema: Dict,
    chart_style: str = "publication",
    enable_statistics: bool = True,
    selected_chart_types: List[str] = []
) -> str:
    """
    构建科研级图表生成 Prompt
    
    Args:
        user_request: 用户需求
        selected_columns: 选择的字段
        data_schema: 数据schema
        chart_style: 图表样式 (publication/presentation/web)
        enable_statistics: 是否启用统计分析
        selected_chart_types: 用户选择的图表类型列表（经典模式专用）
    """
    
    # 获取样式配置
    style_config = RESEARCH_CHART_CONFIGS.get(chart_style, RESEARCH_CHART_CONFIGS["publication"])
    
    # 构建字段信息
    columns_info = []
    for col_name in selected_columns:
        col_info = data_schema['columns'].get(col_name, {})
        col_type = col_info.get('type', 'unknown')
        col_desc = f"- {col_name} ({col_type})"
        
        if 'stats' in col_info:
            stats = col_info['stats']
            if col_type in ['int', 'float']:
                col_desc += f" [范围: {stats.get('min')} - {stats.get('max')}, 平均: {stats.get('mean'):.2f}]"
            elif col_type == 'string':
                col_desc += f" [唯一值: {stats.get('unique')}]"
        
        columns_info.append(col_desc)
    
    columns_str = '\n'.join(columns_info)
    
    # 统计分析部分
    statistics_section = ""
    if enable_statistics:
        statistics_section = """
### 📊 统计分析功能

当用户需要统计检验时，请自动选择合适的方法：

**1. 组间比较**：
- 两组比较：
  - 数据正态 → 独立样本t检验 (scipy.stats.ttest_ind)
  - 数据非正态 → Mann-Whitney U检验 (scipy.stats.mannwhitneyu)
- 多组比较：
  - 数据正态 → 单因素ANOVA (scipy.stats.f_oneway)
  - 数据非正态 → Kruskal-Wallis H检验 (scipy.stats.kruskal)

**2. 相关性分析**：
- Pearson相关 (scipy.stats.pearsonr) - 线性关系
- Spearman相关 (scipy.stats.spearmanr) - 单调关系

**3. 正态性检验**：
- Shapiro-Wilk检验 (scipy.stats.shapiro)

**4. 效应量计算**：
- Cohen's d = (mean1 - mean2) / pooled_std

**5. 结果报告格式**（APA格式）：
```
t(自由度) = t值, p = p值, d = 效应量
示例: t(98) = 3.45, p = 0.001, d = 0.68
```
"""
    
    # 图表类型推荐
    chart_recommendations = """
### 📈 科研图表类型选择指南

根据数据类型和分析目标选择合适的图表：

**1. 数据分布和对比**：
- 箱线图 (Box Plot): 显示分位数、中位数、异常值
- 小提琴图 (Violin Plot): 显示完整的概率密度分布
- 直方图 + 密度曲线: 展示数据分布形状

**2. 组间对比**：
- 柱状图 (Bar Plot): 类别间均值对比
- 点图 (Point Plot): 显示均值和置信区间
- 分组箱线图: 多组分布对比

**3. 相关性分析**：
- 散点图 (Scatter Plot): 两变量关系
- 热力图 (Heatmap): 多变量相关矩阵
- 散点矩阵图 (Pair Plot): 多变量两两关系

**4. 统计模型诊断**：
- QQ图: 正态性检验
- 残差图: 回归诊断
- ROC曲线: 分类模型评估

**5. 医学/生物统计**：
- 生存曲线 (Kaplan-Meier): 生存分析
- 森林图 (Forest Plot): Meta分析
- 韦恩图 (Venn Diagram): 集合关系

**6. 流程和关系**：
- 桑基图 (Sankey): 流向分析
- 雷达图 (Radar): 多维度对比
"""
    
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
   - 每个图表应该完整独立，包含统计分析
"""
    
    prompt = f"""
你是一个专业的科研数据可视化专家，精通统计学和数据分析。

【任务】
根据用户需求生成**高质量科研级**的Python代码，用于数据分析和可视化。

【数据信息】
- DataFrame 变量名：df
- 总行数：{data_schema.get('total_rows', 'unknown')}
- 总列数：{data_schema.get('total_columns', 'unknown')}
- 用户选择的字段：
{columns_str}

【用户需求】
{user_request}
{chart_types_section}
【图表样式】: {style_config['name']}
- 说明：{style_config['description']}
- DPI：{style_config['config']['dpi']}
- 图表尺寸：{style_config['config']['figure_size']}
- 字体：{style_config['config']['font_family']}

{statistics_section}

{chart_recommendations}

【代码规范】

**⚠️ 重要：必须正确输出结果**
- **所有 print 输出必须使用 Markdown 格式**
- **图表必须使用 `display(Image(...))` 显示**
- **不要忘记 `import io` 和 `from IPython.display import Image, display`**
- **必须配置中文字体，否则中文会显示为方框**

**1. 图表配置（出版级质量，支持中文）**：
```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats
import io
from IPython.display import Image, display

# ⚠️ 关键：配置中文字体（必须在最开始配置）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示为方框的问题

# 设置图表样式
plt.rcParams['font.size'] = {style_config['config']['font_size']}
plt.rcParams['figure.dpi'] = {style_config['config']['dpi']}

# 创建图表
fig, ax = plt.subplots(figsize={style_config['config']['figure_size']})

# ... 绘图代码 ...

# 设置轴标签（⚠️ 重要：显式指定fontproperties确保中文显示）
# 示例：ax.set_xlabel('你的X轴标签', fontproperties='SimHei')
# 示例：ax.set_ylabel('你的Y轴标签', fontproperties='SimHei')
# 或者使用 fontdict：ax.set_ylabel('标签', fontdict={{'family': 'SimHei'}})

# 移除顶部和右侧边框（科研风格）
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 添加网格（可选）
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()

# ⚠️ 关键：必须这样保存和显示图表
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi={style_config['config']['dpi']}, bbox_inches='tight')
buf.seek(0)
plt.close()
display(Image(buf.getvalue()))  # 必须使用 display(Image(...))
```

**2. 统计分析示例（必须使用 Markdown 格式输出）**：
```python
# 正态性检验
stat, p_value = stats.shapiro(data)

# 组间比较（t检验）
group1 = df[df['group'] == 'A']['value']
group2 = df[df['group'] == 'B']['value']
t_stat, p_value = stats.ttest_ind(group1, group2)

# 效应量（Cohen's d）
pooled_std = np.sqrt(((len(group1)-1)*group1.std()**2 + (len(group2)-1)*group2.std()**2) / (len(group1)+len(group2)-2))
cohens_d = (group1.mean() - group2.mean()) / pooled_std

# ⚠️ 关键：使用 Markdown 格式输出（一次性 print）
conclusion = "显著差异" if p_value < 0.05 else "无显著差异"
df_value = len(group1) + len(group2) - 2
print(f\"\"\"
## 📊 统计分析结果

### 正态性检验
- Shapiro-Wilk检验: W = {{{{stat:.4f}}}}, p = {{{{p_value:.4f}}}}

### 组间比较（独立样本t检验）
- **t({{{{df_value}}}}) = {{{{t_stat:.2f}}}}, p = {{{{p_value:.4f}}}}, d = {{{{cohens_d:.2f}}}}**
- 结论: {{{{conclusion}}}} (α = 0.05)
\"\"\")
```

**3. 高级图表示例**：

**箱线图 + 统计标注（完整的自包含代码示例）**：
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import io
from IPython.display import Image, display

# ⚠️ 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 假设数据已经加载为 df
# 提取分组数据
group1 = df[df['专业'] == '金融系']['薪资']
group2 = df[df['专业'] == '信息管理与信息系统']['薪资']

# 统计检验（完整计算，不依赖外部变量）
t_stat, p_value = stats.ttest_ind(group1, group2)
effect_size = (group1.mean() - group2.mean()) / np.sqrt((group1.std()**2 + group2.std()**2) / 2)

# 输出统计结果（使用 f-string 格式化）
interpretation = "显著差异" if p_value < 0.05 else "无显著差异"
print(f\"\"\"
## 📊 统计分析结果

**组间差异检验 (Independent t-test)**
- t 统计量: {{{{t_stat:.4f}}}}
- p 值: {{{{p_value:.4f}}}}
- Cohen's d (效应量): {{{{effect_size:.4f}}}}

**解释**: {{{{interpretation}}}} (α=0.05)
\"\"\")

# 绘制箱线图
fig, ax = plt.subplots(figsize=(8, 6))
sns.boxplot(data=df, x='专业', y='薪资', ax=ax, palette='Set2')
sns.swarmplot(data=df, x='专业', y='薪资', ax=ax, color='black', alpha=0.5, size=3)

# 添加统计显著性标注
if p_value < 0.001:
    sig_symbol = '***'
elif p_value < 0.01:
    sig_symbol = '**'
elif p_value < 0.05:
    sig_symbol = '*'
else:
    sig_symbol = 'ns'

y_max = df['薪资'].max()
ax.plot([0, 1], [y_max*1.05, y_max*1.05], 'k-', linewidth=1.5)
ax.text(0.5, y_max*1.08, sig_symbol, ha='center', fontsize=16)

# ⚠️ 设置中文标签
ax.set_xlabel('专业', fontsize=12, fontproperties='SimHei')
ax.set_ylabel('薪资（元/月）', fontsize=12, fontproperties='SimHei')
ax.set_title('不同专业薪资对比', fontsize=14, fontproperties='SimHei')
plt.xticks(fontproperties='SimHei')
plt.tight_layout()

# 保存并显示
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
buf.seek(0)
display(Image(buf.getvalue()))
plt.close()
```

**关键点**：
- ✅ 代码中直接计算了 `t_stat` 和 `p_value`，没有引用外部变量
- ✅ 包含了数据提取、统计计算、绘图的完整流程
- ✅ 可以独立执行，不依赖之前的代码步骤

**小提琴图**：
```python
fig, ax = plt.subplots(figsize=(8, 6))
parts = ax.violinplot([group1, group2], positions=[1, 2], 
                       showmeans=True, showmedians=True)

# 美化小提琴图
for pc in parts['bodies']:
    pc.set_facecolor('#8dd3c7')
    pc.set_alpha(0.7)

ax.set_xticks([1, 2])
ax.set_xticklabels(['Group A', 'Group B'])
```

**热力图（相关性矩阵）**：
```python
# 计算相关系数
corr_matrix = df[numeric_columns].corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, linewidths=1, cbar_kws={{"shrink": 0.8}})
plt.title('Correlation Matrix', fontsize=14, pad=20)
plt.tight_layout()
```

**QQ图（正态性检验）**：
```python
from scipy import stats

fig, ax = plt.subplots(figsize=(6, 6))
stats.probplot(df['value'], dist="norm", plot=ax)
ax.set_title('Q-Q Plot')
ax.grid(True, alpha=0.3)
```

**4. 完整代码示例模板（⚠️ 必须包含中文字体配置）**：
```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats
import io
from IPython.display import Image, display

# ⚠️ 第一步：配置中文字体（必须！）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 设置图表样式
plt.rcParams['font.size'] = {style_config['config']['font_size']}
plt.rcParams['figure.dpi'] = {style_config['config']['dpi']}

# 数据分析（示例）
print(f\"\"\"
## 📊 数据概览
- 总样本数: {{{{len(df)}}}}
- 分析字段: ...
\"\"\")

# 创建图表
fig, ax = plt.subplots(figsize={style_config['config']['figure_size']})
# ... 你的绘图代码 ...
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()

# 显示图表（⚠️ 必须这样做）
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi={style_config['config']['dpi']}, bbox_inches='tight')
buf.seek(0)
plt.close()
display(Image(buf.getvalue()))

# 统计结果（使用 f-string）
print(f\"\"\"
## 📈 统计结果
- t检验: p = {{{{p_value:.4f}}}}
\"\"\")
```

**5. 输出要求**：
- ⚠️ **必须使用 print() 输出文本**
- ⚠️ **必须使用 display(Image(...)) 显示图表**
- 所有统计结果使用 Markdown 格式
- p值小于0.001时标记为 p < 0.001
- 保留2-4位有效数字
- 添加清晰的图表标题和轴标签

**6. 限制**：
- 最多生成 1-2 个图表
- 最多 3-5 个 print 语句
- 不要在循环中使用 print
- 使用 f-string 三引号合并输出

【输出格式】
只输出纯 Python 代码，不要有任何解释文字。

【代码自包含性】⚠️ 非常重要：
生成的代码必须是**完整的、可独立执行的**，不能依赖之前步骤的变量！
- ✅ 正确：代码包含从数据加载、统计计算到绘图的完整流程
- ❌ 错误：代码引用了之前计算的变量（如 t_stat、p_value 等）

【代码检查清单】⚠️ 生成代码前必须确认：
✅ 导入了 `import io`
✅ 导入了 `from IPython.display import Image, display`
✅ **配置了中文字体**: `plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', ...]`
✅ **设置了负号**: `plt.rcParams['axes.unicode_minus'] = False`
✅ **轴标签使用中文时，显式指定字体**: `ax.set_xlabel('标签', fontproperties='SimHei')`
✅ **标题使用中文时，也要指定字体**: `ax.set_title('标题', fontproperties='SimHei')`
✅ 使用 `print()` 输出了分析结果（Markdown格式）
✅ 使用 `display(Image(buf.getvalue()))` 显示了图表
✅ 代码结构完整，没有遗漏关键步骤

【特别提醒】
⚠️ 如果用户的需求模糊（如"分析数据"、"画图"），请主动判断：
1. 查看数据类型（连续型/分类型）
2. 识别分组变量
3. 选择最合适的可视化方法
4. 如果有2个以上分组，自动进行统计检验

⚠️ **最重要的注意事项**：
1. **中文字体设置**：
   - 必须在开头配置：`plt.rcParams['font.sans-serif'] = ['SimHei', ...]`
   - 所有中文标签必须显式指定：`ax.set_xlabel('标签', fontproperties='SimHei')`
   - 标题也要指定：`ax.set_title('标题', fontproperties='SimHei')`
   
2. **确保有输出**：
   - 至少要有 1 个 print 语句
   - 或者至少要有 1 个 display(Image(...))
   - 否则前端会显示"未捕获到输出"

3. **完整的中文图表示例**：
   ```python
   # 配置字体
   plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
   plt.rcParams['axes.unicode_minus'] = False
   
   # 绘图
   fig, ax = plt.subplots(figsize=(10, 6))
   ax.plot(x, y)
   
   # 设置中文标签（关键！）
   ax.set_xlabel('X轴标签', fontproperties='SimHei', fontsize=12)
   ax.set_ylabel('Y轴标签', fontproperties='SimHei', fontsize=12)
   ax.set_title('图表标题', fontproperties='SimHei', fontsize=14)
   
   # 如果有图例，也要设置字体
   ax.legend(['数据1', '数据2'], prop={{'family': 'SimHei'}})
   ```
"""
    
    return prompt.strip()


def build_chart_type_detection_prompt(user_request: str, data_schema: Dict) -> str:
    """
    构建图表类型检测 Prompt
    用于 AI 判断用户想要什么类型的图表
    """
    
    prompt = f"""
你是一个数据可视化专家。请根据用户需求判断最合适的图表类型。

【用户需求】
{user_request}

【数据信息】
- 总行数：{data_schema.get('total_rows', 'unknown')}
- 字段类型分布：
  - 数值型字段：{len([c for c in data_schema.get('columns', {}).values() if c.get('type') in ['int', 'float']])} 个
  - 文本型字段：{len([c for c in data_schema.get('columns', {}).values() if c.get('type') == 'string'])} 个

【任务】
请判断用户最可能需要的图表类型，从以下选项中选择1-2个最合适的：

1. box_plot - 箱线图（适合：组间对比、异常值检测）
2. violin_plot - 小提琴图（适合：分布对比）
3. scatter_plot - 散点图（适合：相关性分析）
4. heatmap - 热力图（适合：相关矩阵、混淆矩阵）
5. bar_plot - 柱状图（适合：分类统计）
6. histogram - 直方图（适合：数据分布）
7. line_plot - 折线图（适合：时间序列）
8. pair_plot - 散点矩阵图（适合：多变量探索）
9. qq_plot - QQ图（适合：正态性检验）
10. survival_curve - 生存曲线（适合：医学统计）

【输出格式】
仅输出JSON格式，不要有其他文字：
{{
    "primary_chart": "图表类型",
    "secondary_chart": "备选图表类型或null",
    "reasoning": "选择原因（1句话）",
    "requires_statistics": true/false,
    "suggested_style": "publication/presentation/web"
}}
"""
    
    return prompt.strip()


def get_chart_template(chart_type: str) -> str:
    """
    获取图表代码模板
    """
    templates = {
        "box_plot": """
# 箱线图
fig, ax = plt.subplots(figsize=(8, 6))
bp = ax.boxplot([data1, data2], labels=['Group A', 'Group B'], 
                 patch_artist=True, widths=0.6)
for patch in bp['boxes']:
    patch.set_facecolor('#8dd3c7')
ax.set_ylabel('Value')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
""",
        "violin_plot": """
# 小提琴图  
fig, ax = plt.subplots(figsize=(8, 6))
parts = ax.violinplot([data1, data2], positions=[1, 2], 
                       showmeans=True, showmedians=True)
for pc in parts['bodies']:
    pc.set_facecolor('#8dd3c7')
    pc.set_alpha(0.7)
""",
        "heatmap": """
# 热力图
corr = df.corr()
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
plt.colorbar(im, ax=ax)
""",
        "qq_plot": """
# QQ图
from scipy import stats
fig, ax = plt.subplots(figsize=(6, 6))
stats.probplot(data, dist="norm", plot=ax)
ax.set_title('Normal Q-Q Plot')
"""
    }
    
    return templates.get(chart_type, "# 自定义图表代码")

