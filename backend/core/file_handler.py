"""
文件处理模块
"""
import os
import uuid
import math
import pandas as pd
import numpy as np
import logging
from datetime import datetime, date, time
from typing import Dict, Any, List
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

# 配置常量
SAMPLE_SIZE = 5000  # 采样行数（用于分析）
PREVIEW_SIZE = 100  # 预览行数（用于前端显示）
LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB，超过此大小使用采样模式


class FileHandler:
    """文件处理器"""
    
    @staticmethod
    async def save_uploaded_file(file_content: bytes, filename: str) -> str:
        """
        保存上传的文件
        
        Returns:
            file_id
        """
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix
        
        # 保存文件
        file_path = os.path.join(settings.upload_dir, f"{file_id}{file_ext}")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"文件已保存: {file_path}")
        return file_id
    
    @staticmethod
    def _parse_dataframe(df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """
        解析单个 DataFrame
        
        Returns:
            {
                'sheet_name': str,
                'total_rows': int,
                'total_columns': int,
                'columns': [{name, type, nullable, stats}, ...],
                'preview': [...],
                'data_json': str
            }
        """
        total_rows, total_columns = df.shape
        
        # 提取列信息
        columns_info = []
        for col_name in df.columns:
            col_data = df[col_name]
            
            # 数据类型
            dtype = str(col_data.dtype)
            if dtype.startswith('int'):
                col_type = 'int'
            elif dtype.startswith('float'):
                col_type = 'float'
            elif dtype == 'bool':
                col_type = 'bool'
            elif dtype == 'datetime64':
                col_type = 'datetime'
            else:
                col_type = 'string'
            
            # 是否可空
            nullable = col_data.isnull().any()
            
            # 统计信息
            stats = {}
            if col_type in ['int', 'float']:
                # 处理数值型字段，将 NaN 转换为 None
                def safe_float(value):
                    """安全转换 float，NaN 转为 None"""
                    if pd.isna(value):
                        return None
                    try:
                        return float(value)
                    except:
                        return None
                
                # 先去除 NaN 值，避免警告
                valid_data = col_data.dropna()
                
                if len(valid_data) > 0:
                    stats = {
                        'min': safe_float(valid_data.min()),
                        'max': safe_float(valid_data.max()),
                        'mean': safe_float(valid_data.mean()),
                        'median': safe_float(valid_data.median()),
                        'std': safe_float(valid_data.std()),
                    }
                else:
                    # 如果列全是 NaN，统计值都为 None
                    stats = {
                        'min': None,
                        'max': None,
                        'mean': None,
                        'median': None,
                        'std': None,
                    }
            elif col_type == 'string':
                # 处理字符串型字段，过滤掉 NaN
                unique_values = col_data.dropna().unique()
                # 转换为 Python 原生类型，处理 NaN
                sample_values = []
                for val in unique_values[:5]:
                    if pd.notna(val):
                        sample_values.append(str(val))
                
                stats = {
                    'unique': len(unique_values),
                    'sample': sample_values,
                }
            
            columns_info.append({
                'name': col_name,
                'type': col_type,
                'nullable': bool(nullable),
                'stats': stats
            })
        
        # 数据预览（前100行）
        # 将 NaN 替换为 None，以便 JSON 序列化
        preview_df = df.head(100)
        # 直接转换为字典，不需要 fillna
        preview = preview_df.to_dict(orient='records')
        
        # 递归清理所有不可序列化的值
        def clean_nan(obj):
            """递归清理对象中的所有不可序列化的值（NaN, Timestamp, datetime等）"""
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            elif pd.isna(obj):
                # 处理所有类型的 NaN（包括 pd.NaT）
                return None
            elif isinstance(obj, (pd.Timestamp, np.datetime64, datetime, date, time)):
                # 将各种 datetime 类型转换为 ISO 格式字符串
                try:
                    return obj.isoformat()
                except:
                    return str(obj)
            elif hasattr(obj, 'item'):
                # NumPy 类型（如 np.int64）转换为 Python 原生类型
                return obj.item()
            else:
                return obj
        
        preview = clean_nan(preview)
        
        # 完整数据的 JSON（用于 Jupyter Kernel）
        # 使用 pandas 的 to_json，会自动处理 NaN
        data_json = df.to_json(orient='records', force_ascii=False, date_format='iso')
        
        return {
            'sheet_name': sheet_name,
            'total_rows': total_rows,
            'total_columns': total_columns,
            'columns': columns_info,
            'preview': preview,
            'data_json': data_json
        }
    
    @staticmethod
    def parse_file(file_id: str, filename: str) -> Dict[str, Any]:
        """
        解析文件并提取信息（支持多工作表）
        
        Returns:
            {
                'file_id': str,
                'file_name': str,
                'file_size': int,
                'sheets': [
                    {
                        'sheet_name': str,
                        'total_rows': int,
                        'total_columns': int,
                        'columns': [{name, type, nullable, stats}, ...],
                        'preview': [...],
                        'data_json': str
                    },
                    ...
                ]
            }
        """
        # 构建文件路径
        file_ext = Path(filename).suffix
        file_path = os.path.join(settings.upload_dir, f"{file_id}{file_ext}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始解析文件: {file_path}")
        
        file_size = os.path.getsize(file_path)
        sheets_data = []
        
        # 根据文件类型读取
        if file_ext in ['.xlsx', '.xls']:
            # Excel 文件：读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            logger.info(f"Excel 文件包含 {len(excel_file.sheet_names)} 个工作表: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                # 先读取小样本判断大小
                df_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1000)
                estimated_total_rows = len(df_sample)  # 临时估算
                
                # 判断是否为大文件（Excel 通常较小，阈值可以更宽松）
                if file_size > LARGE_FILE_THRESHOLD * 2:  # Excel 阈值为 100MB
                    logger.info(f"Excel 大文件检测，工作表 '{sheet_name}'")
                    # 读取全部数据后采样
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if len(df) > SAMPLE_SIZE:
                        logger.info(f"工作表 '{sheet_name}' 过大（{len(df)} 行），使用采样")
                        sheet_data = FileHandler._parse_large_dataframe_sampling(df, sheet_name)
                    else:
                        sheet_data = FileHandler._parse_dataframe(df, sheet_name)
                else:
                    # 正常大小，全量读取
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    logger.info(f"工作表 '{sheet_name}' 数据形状: {df.shape}")
                    sheet_data = FileHandler._parse_dataframe(df, sheet_name)
                
                sheets_data.append(sheet_data)
                
        elif file_ext == '.csv':
            # CSV 文件：只有一个表
            # 检查文件大小，决定是否使用采样模式
            if file_size > LARGE_FILE_THRESHOLD:
                logger.info(f"大文件检测：{file_size / 1024 / 1024:.2f} MB，使用采样模式")
                sheet_data = FileHandler._parse_large_csv_streaming(file_path, "Sheet1")
            else:
                # 小文件：全量读取
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except:
                        df = pd.read_csv(file_path, encoding='latin1')
                
                logger.info(f"CSV 文件解析成功，数据形状: {df.shape}")
                sheet_data = FileHandler._parse_dataframe(df, "Sheet1")
            
            sheets_data.append(sheet_data)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        result = {
            'file_id': file_id,
            'file_name': filename,
            'file_size': file_size,
            'sheets': sheets_data
        }
        
        logger.info(f"文件解析完成，共 {len(sheets_data)} 个工作表")
        return result
    
    @staticmethod
    def _parse_large_dataframe_sampling(df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """
        对已加载的大 DataFrame 进行采样（用于 Excel）
        """
        total_rows = len(df)
        print(f"🚀 [DataFrame 采样] 开始处理: {sheet_name}, 总行数: {total_rows:,}")
        
        # 随机采样
        if total_rows > SAMPLE_SIZE:
            df_sample = df.sample(n=SAMPLE_SIZE, random_state=42)
            print(f"📌 [DataFrame 采样] 已采样 {SAMPLE_SIZE:,} 行 ({SAMPLE_SIZE/total_rows*100:.1f}%)")
        else:
            df_sample = df
        
        # 生成列信息
        columns_info = []
        for col_name in df.columns:
            col_data = df[col_name]
            col_sample = df_sample[col_name]
            
            # 数据类型
            dtype = str(col_data.dtype)
            if dtype.startswith('int'):
                col_type = 'int'
            elif dtype.startswith('float'):
                col_type = 'float'
            elif dtype == 'bool':
                col_type = 'bool'
            else:
                col_type = 'string'
            
            # 统计信息（使用全量数据）
            stats = {}
            if col_type in ['int', 'float']:
                valid_data = col_data.dropna()
                if len(valid_data) > 0:
                    stats = {
                        'min': float(valid_data.min()) if not pd.isna(valid_data.min()) else None,
                        'max': float(valid_data.max()) if not pd.isna(valid_data.max()) else None,
                        'mean': float(valid_data.mean()) if not pd.isna(valid_data.mean()) else None,
                    }
            elif col_type == 'string':
                unique_vals = col_sample.dropna().unique()
                stats = {
                    'unique': len(unique_vals),
                    'sample': list(unique_vals[:5])
                }
            
            columns_info.append({
                'name': col_name,
                'type': col_type,
                'nullable': col_data.isnull().any(),
                'stats': stats
            })
        
        # 生成预览
        preview_df = df_sample.head(PREVIEW_SIZE)
        preview = preview_df.to_dict(orient='records')
        
        # 清理不可序列化的值
        def clean_nan(obj):
            """递归清理对象中的所有不可序列化的值（NaN, Timestamp, datetime等）"""
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            elif pd.isna(obj):
                # 处理所有类型的 NaN（包括 pd.NaT）
                return None
            elif isinstance(obj, (pd.Timestamp, np.datetime64, datetime, date, time)):
                # 将各种 datetime 类型转换为 ISO 格式字符串
                try:
                    return obj.isoformat()
                except:
                    return str(obj)
            elif hasattr(obj, 'item'):
                return obj.item()
            else:
                return obj
        
        preview = clean_nan(preview)
        
        # data_json
        data_json = df_sample.to_json(orient='records', force_ascii=False, date_format='iso')
        
        print(f"✅ [DataFrame 采样] 处理完成")
        
        return {
            'sheet_name': sheet_name,
            'total_rows': total_rows,
            'total_columns': len(df.columns),
            'columns': columns_info,
            'preview': preview,
            'data_json': data_json,
            'is_sampled': total_rows > SAMPLE_SIZE,
            'sample_size': len(df_sample)
        }
    
    @staticmethod
    def _parse_large_csv_streaming(file_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        流式解析大 CSV 文件（采样模式）
        
        策略：
        1. 快速计数总行数
        2. 随机采样 SAMPLE_SIZE 行用于分析
        3. 流式计算统计信息
        """
        print(f"🚀 [大文件处理] 开始流式解析: {file_path}")
        
        # 第1步：快速获取总行数和列名
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取表头
            header = f.readline().strip().split(',')
            # 快速计数
            total_rows = sum(1 for _ in f)
        
        print(f"📊 [大文件处理] 总行数: {total_rows:,}, 列数: {len(header)}")
        
        # 第2步：智能采样（如果数据量太大）
        if total_rows > SAMPLE_SIZE:
            # 计算采样率
            skip_prob = 1 - (SAMPLE_SIZE / total_rows)
            print(f"📌 [大文件处理] 采样模式：保留 {SAMPLE_SIZE:,} 行 ({SAMPLE_SIZE/total_rows*100:.1f}%)")
            
            # 随机采样
            df_sample = pd.read_csv(
                file_path,
                skiprows=lambda i: i > 0 and np.random.random() < skip_prob
            )
        else:
            # 数据量适中，全量读取
            df_sample = pd.read_csv(file_path)
        
        print(f"✅ [大文件处理] 采样完成：{len(df_sample)} 行")
        
        # 第3步：流式计算精确统计（遍历所有数据）
        print(f"📈 [大文件处理] 开始流式统计计算...")
        streaming_stats = FileHandler._calculate_streaming_stats(file_path)
        
        # 第4步：使用采样数据生成列信息（结合流式统计）
        columns_info = []
        for col_name in df_sample.columns:
            col_data = df_sample[col_name]
            
            # 数据类型
            dtype = str(col_data.dtype)
            if dtype.startswith('int'):
                col_type = 'int'
            elif dtype.startswith('float'):
                col_type = 'float'
            elif dtype == 'bool':
                col_type = 'bool'
            else:
                col_type = 'string'
            
            # 统计信息（优先使用流式统计的精确值）
            stats = {}
            if col_name in streaming_stats:
                stats = streaming_stats[col_name]
            elif col_type in ['int', 'float']:
                valid_data = col_data.dropna()
                if len(valid_data) > 0:
                    stats = {
                        'min': float(valid_data.min()) if not pd.isna(valid_data.min()) else None,
                        'max': float(valid_data.max()) if not pd.isna(valid_data.max()) else None,
                        'mean': float(valid_data.mean()) if not pd.isna(valid_data.mean()) else None,
                    }
            elif col_type == 'string':
                unique_vals = col_data.dropna().unique()
                stats = {
                    'unique': len(unique_vals),
                    'sample': list(unique_vals[:5])
                }
            
            columns_info.append({
                'name': col_name,
                'type': col_type,
                'nullable': col_data.isnull().any(),
                'stats': stats
            })
        
        # 第5步：生成预览和数据 JSON（只用采样数据）
        preview_df = df_sample.head(PREVIEW_SIZE)
        preview = preview_df.to_dict(orient='records')
        
        # 清理不可序列化的值
        def clean_nan(obj):
            """递归清理对象中的所有不可序列化的值（NaN, Timestamp, datetime等）"""
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            elif pd.isna(obj):
                # 处理所有类型的 NaN（包括 pd.NaT）
                return None
            elif isinstance(obj, (pd.Timestamp, np.datetime64, datetime, date, time)):
                # 将各种 datetime 类型转换为 ISO 格式字符串
                try:
                    return obj.isoformat()
                except:
                    return str(obj)
            elif hasattr(obj, 'item'):
                return obj.item()
            else:
                return obj
        
        preview = clean_nan(preview)
        
        # data_json 只保存采样数据（用于 Jupyter 分析）
        data_json = df_sample.to_json(orient='records', force_ascii=False, date_format='iso')
        
        print(f"✅ [大文件处理] 解析完成")
        
        return {
            'sheet_name': sheet_name,
            'total_rows': total_rows,
            'total_columns': len(header),
            'columns': columns_info,
            'preview': preview,
            'data_json': data_json,
            'is_sampled': total_rows > SAMPLE_SIZE,  # 标记是否采样
            'sample_size': len(df_sample)  # 实际采样行数
        }
    
    @staticmethod
    def _calculate_streaming_stats(file_path: str, chunk_size: int = 10000) -> Dict[str, Dict]:
        """流式计算统计信息（不占用大量内存）"""
        stats = {}
        
        try:
            for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
                for col in chunk.columns:
                    if col not in stats:
                        stats[col] = {
                            'min': float('inf'),
                            'max': float('-inf'),
                            'sum': 0,
                            'count': 0
                        }
                    
                    if pd.api.types.is_numeric_dtype(chunk[col]):
                        valid_data = chunk[col].dropna()
                        if len(valid_data) > 0:
                            stats[col]['min'] = min(stats[col]['min'], valid_data.min())
                            stats[col]['max'] = max(stats[col]['max'], valid_data.max())
                            stats[col]['sum'] += valid_data.sum()
                            stats[col]['count'] += len(valid_data)
                
                # 每处理10个chunk打印一次进度
                if i % 10 == 0 and i > 0:
                    print(f"📊 [流式统计] 已处理 {(i+1)*chunk_size:,} 行...")
        
        except Exception as e:
            print(f"⚠️ [流式统计] 警告: {e}，跳过流式统计")
            return {}
        
        # 计算平均值
        for col, col_stats in stats.items():
            if col_stats['count'] > 0:
                col_stats['mean'] = col_stats['sum'] / col_stats['count']
                # 清理无穷大值
                if math.isinf(col_stats['min']):
                    col_stats['min'] = None
                if math.isinf(col_stats['max']):
                    col_stats['max'] = None
                del col_stats['sum']  # 删除中间变量
        
        return stats
    
    @staticmethod
    def get_file_path(file_id: str, filename: str) -> str:
        """获取文件路径"""
        file_ext = Path(filename).suffix
        return os.path.join(settings.upload_dir, f"{file_id}{file_ext}")


# 全局实例
file_handler = FileHandler()

