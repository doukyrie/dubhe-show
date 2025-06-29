import os
import json
from core import DataParser
from typing import Dict, Any, List, Optional
from io import BytesIO
import base64
from datetime import datetime
import numpy as np
from PIL import Image

class JSONParser(DataParser):

    @staticmethod
    def supported_extensions():
        return ['.json']

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取文件基本信息
            file_size = os.path.getsize(file_path)
            creation_time = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            modification_time = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

            # 分析JSON数据结构
            structure_info = self._analyze_structure(data)

            # 尝试提取缩略图（如果数据中包含图像数据）
            thumbnail_base64 = self._try_extract_thumbnail(data)

            return {
                "filename": os.path.basename(file_path),
                "data_type": "json",
                "format": "JSON",
                "source": file_path,
                "size": file_size,
                "structure": structure_info,
                "depth": self._get_depth(data),
                "value_types": self._get_value_types(data),
                "array_stats": self._get_array_stats(data),
                "object_stats": self._get_object_stats(data),
                "creation_time": creation_time,
                "modification_time": modification_time,
                "metadata": {
                    "encoding": "utf-8",
                    "is_valid": True
                },
                "tags": ["structured", "text"],
                "thumbnail_base64": thumbnail_base64,
                "content_sample": self._get_content_sample(data)
            }
        except Exception as e:
            return None

    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """分析JSON数据结构"""
        if isinstance(data, dict):
            return {
                "type": "object",
                "key_count": len(data),
                "key_types": {k: type(v).__name__ for k, v in data.items()},
                "nested": {k: self._analyze_structure(v) for k, v in data.items()}
            }
        elif isinstance(data, list):
            if len(data) > 0:
                sample_type = type(data[0]).__name__
                uniform = all(isinstance(x, type(data[0])) for x in data)
            else:
                sample_type = "empty"
                uniform = True
            return {
                "type": "array",
                "length": len(data),
                "sample_type": sample_type,
                "is_uniform": uniform,
                "first_item": self._analyze_structure(data[0]) if len(data) > 0 else None
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:100] + ("..." if len(str(data)) > 100 else "")
            }

    def _get_depth(self, data: Any, current_depth: int = 0) -> int:
        """计算JSON最大嵌套深度"""
        if isinstance(data, dict):
            return max((self._get_depth(v, current_depth + 1) for v in data.values()), default=current_depth)
        elif isinstance(data, list):
            return max((self._get_depth(item, current_depth + 1) for item in data), default=current_depth)
        else:
            return current_depth

    def _get_value_types(self, data: Any) -> Dict[str, int]:
        """统计所有值的类型"""
        type_counts = {
            "dict": 0,
            "list": 0,
            "str": 0,
            "int": 0,
            "float": 0,
            "bool": 0,
            "null": 0
        }

        def _count_types(item):
            if isinstance(item, dict):
                type_counts["dict"] += 1
                for v in item.values():
                    _count_types(v)
            elif isinstance(item, list):
                type_counts["list"] += 1
                for i in item:
                    _count_types(i)
            elif isinstance(item, str):
                type_counts["str"] += 1
            elif isinstance(item, bool):
                type_counts["bool"] += 1
            elif isinstance(item, int):
                type_counts["int"] += 1
            elif isinstance(item, float):
                type_counts["float"] += 1
            elif item is None:
                type_counts["null"] += 1

        _count_types(data)
        return type_counts

    def _get_array_stats(self, data: Any) -> Dict[str, Any]:
        """获取数组统计信息"""
        stats = {
            "max_length": 0,
            "min_length": float('inf'),
            "total_arrays": 0,
            "total_items": 0
        }

        def _scan(item):
            if isinstance(item, list):
                stats["total_arrays"] += 1
                stats["total_items"] += len(item)
                stats["max_length"] = max(stats["max_length"], len(item))
                stats["min_length"] = min(stats["min_length"], len(item))
                for i in item:
                    _scan(i)
            elif isinstance(item, dict):
                for v in item.values():
                    _scan(v)

        _scan(data)
        stats["avg_length"] = stats["total_items"] / stats["total_arrays"] if stats["total_arrays"] > 0 else 0
        return stats

    def _get_object_stats(self, data: Any) -> Dict[str, Any]:
        """获取对象统计信息"""
        stats = {
            "max_keys": 0,
            "min_keys": float('inf'),
            "total_objects": 0,
            "total_keys": 0
        }

        def _scan(item):
            if isinstance(item, dict):
                stats["total_objects"] += 1
                key_count = len(item)
                stats["total_keys"] += key_count
                stats["max_keys"] = max(stats["max_keys"], key_count)
                stats["min_keys"] = min(stats["min_keys"], key_count)
                for v in item.values():
                    _scan(v)
            elif isinstance(item, list):
                for i in item:
                    _scan(i)

        _scan(data)
        stats["avg_keys"] = stats["total_keys"] / stats["total_objects"] if stats["total_objects"] > 0 else 0
        return stats

    def _try_extract_thumbnail(self, data: Any) -> str:
        """尝试从数据中提取图像并生成缩略图"""
        try:
            # 检查是否包含常见的图像数据字段
            image_data = None
            if isinstance(data, dict):
                for field in ['image', 'thumbnail', 'picture', 'img']:
                    if field in data and isinstance(data[field], str):
                        image_data = data[field]
                        break
            
            if image_data and image_data.startswith('data:image'):
                # Base64编码的图像数据
                header, encoded = image_data.split(',', 1)
                img_bytes = base64.b64decode(encoded)
                img = Image.open(BytesIO(img_bytes))
                img.thumbnail((128, 128))
                byte_io = BytesIO()
                img.save(byte_io, format="JPEG")
                return base64.b64encode(byte_io.getvalue()).decode("utf-8")
        except:
            pass
        return ""

    def _get_content_sample(self, data: Any, max_length: int = 200) -> str:
        """获取内容样例"""
        sample = str(data)
        if len(sample) > max_length:
            return sample[:max_length] + "..."
        return sample