from core import DataParser
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import h5py

class HDF5Parser(DataParser):
    """HDF5 科学数据解析器"""

    @staticmethod
    def supported_extensions():
        return [".hdf", ".hdf5", ".he5"]

    def parse(self, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            with h5py.File(file_path, "r") as f:
                metadata = self._get_attrs(f.attrs)
                datasets = self._list_datasets(f)

                # 尝试提取第一个二维图像作为缩略图
                thumbnail_base64 = None
                first_array = self._get_first_2d_array(f)
                if first_array is not None:
                    thumbnail_base64 = self._array_to_thumbnail(first_array)

                return {
                    "filename": os.path.basename(file_path),
                    "data_type": "scientific",
                    "format": "HDF5",
                    "source": file_path,
                    "metadata": {
                        "global_attributes": metadata,
                        "datasets": datasets
                    },
                    "thumbnail_base64": thumbnail_base64,
                    "tags": ["scientific", "multidimensional"]
                }
        except Exception as e:
            return None

    def _get_attrs(self, attrs):
        result = {}
        for k, v in attrs.items():
            try:
                result[k] = v.decode() if isinstance(v, bytes) else v
            except:
                result[k] = str(v)
        return result

    def _list_datasets(self, group, path=""):
        result = []
        for name, item in group.items():
            full_path = f"{path}/{name}"
            if isinstance(item, h5py.Dataset):
                result.append({
                    "name": full_path,
                    "shape": list(item.shape),
                    "dtype": str(item.dtype),
                    "attributes": self._get_attrs(item.attrs)
                })
            elif isinstance(item, h5py.Group):
                result.extend(self._list_datasets(item, full_path))
        return result

    def _get_first_2d_array(self, group, path=""):
        for name, item in group.items():
            full_path = f"{path}/{name}"
            if isinstance(item, h5py.Dataset):
                if len(item.shape) == 2:
                    return item[:]
            elif isinstance(item, h5py.Group):
                result = self._get_first_2d_array(item, full_path)
                if result is not None:
                    return result
        return None

    def _array_to_thumbnail(self, arr: np.ndarray):
        # 归一化
        arr_min, arr_max = np.nanmin(arr), np.nanmax(arr)
        if arr_min == arr_max:
            arr_normalized = np.zeros_like(arr, dtype=np.uint8)
        else:
            arr_normalized = ((arr - arr_min) / (arr_max - arr_min) * 255).astype(np.uint8)

        img = Image.fromarray(arr_normalized)
        img.thumbnail((128, 128))
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

class NetCDFParser(DataParser):
    """NetCDF 科学数据解析器"""

    @staticmethod
    def supported_extensions():
        return [".nc"]

    def parse(self, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            import netCDF4
            with netCDF4.Dataset(file_path, "r") as f:
                metadata = self._get_attrs(f.__dict__)
                variables = self._list_variables(f)

                # 尝试提取第一个二维图像作为缩略图
                thumbnail_base64 = None
                first_array = self._get_first_2d_array(f)
                if first_array is not None:
                    thumbnail_base64 = self._array_to_thumbnail(first_array)

                return {
                    "filename": os.path.basename(file_path),
                    "data_type": "scientific",
                    "format": "NetCDF",
                    "source": file_path,
                    "metadata": {
                        "global_attributes": metadata,
                        "variables": variables
                    },
                    "thumbnail_base64": thumbnail_base64,
                    "tags": ["scientific", "multidimensional"]
                }
        except Exception as e:
            return None

    def _get_attrs(self, attrs_dict):
        result = {}
        for k, v in attrs_dict.items():
            try:
                if isinstance(v, np.ndarray):
                    v = v.tolist()
                result[k] = v
            except:
                result[k] = str(v)
        return result

    def _list_variables(self, dataset):
        result = []
        for var_name in dataset.variables:
            var = dataset.variables[var_name]
            result.append({
                "name": var_name,
                "shape": list(var.shape),
                "dtype": str(var.dtype),
                "dimensions": list(var.dimensions),
                "attributes": self._get_attrs(var.__dict__)
            })
        return result

    def _get_first_2d_array(self, dataset):
        for var_name in dataset.variables:
            var = dataset.variables[var_name]
            if len(var.shape) == 2:
                return var[:]
        return None

    def _array_to_thumbnail(self, arr: np.ndarray):
        # 同 HDF5Parser 的实现
        arr_min, arr_max = np.nanmin(arr), np.nanmax(arr)
        if arr_min == arr_max:
            arr_normalized = np.zeros_like(arr, dtype=np.uint8)
        else:
            arr_normalized = ((arr - arr_min) / (arr_max - arr_min) * 255).astype(np.uint8)

        img = Image.fromarray(arr_normalized)
        img.thumbnail((128, 128))
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
