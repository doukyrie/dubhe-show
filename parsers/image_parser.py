import os
import numpy as np
import base64
from PIL import Image
import json
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core import DataParser
from io import BytesIO
import rasterio

class CommonImageParser(DataParser):
    """支持 JPG, PNG, BMP, GIF, JPEG, WEBP 等常见图像格式"""
    @staticmethod
    def supported_extensions():
        return [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".svg"]

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
                channels = len(img.getbands())
                img_array = np.array(img)
                exif = img._getexif() or {}
                iptc = img.info.get("iptc", {})
                xmp = img.info.get("xml", "")

                dpi = img.info.get("dpi")
                if not dpi or not isinstance(dpi, tuple) or len(dpi) != 2 or isinstance(dpi[0], float):
                    dpi = (72, 72)
                else:
                    # 确保DPI值为正数
                    try:
                        dpi = (
                            int(float(dpi[0])) if float(dpi[0]) > 0 else 72,
                            int(float(dpi[1])) if float(dpi[1]) > 0 else 72
                        )
                    except (ValueError, TypeError):
                        dpi = (72, 72)

                # 提取缩略图 Base64 编码（非“首帧”，而是缩略图）
                thumbnail = img.copy()
                thumbnail.thumbnail((128, 128))
                img_byte_arr = BytesIO()
                thumbnail.save(img_byte_arr, format=img.format)
                thumbnail_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

                # 处理 metadata 中的不可序列化数据
                def sanitize_metadata(data):
                    if isinstance(data, (str, int, float, bool)) or data is None:
                        return data
                    elif isinstance(data, (tuple, list)):
                        return [sanitize_metadata(item) for item in data]
                    elif isinstance(data, dict):
                        return {str(k): sanitize_metadata(v) for k, v in data.items()}
                    else:
                        try:
                            # 尝试序列化，如果失败则转为字符串
                            json.dumps(data)
                            return data
                        except (TypeError, ValueError):
                            return str(data)

                # 处理各 metadata 字段
                safe_exif = sanitize_metadata(exif)
                safe_iptc = sanitize_metadata(iptc)
                safe_xmp = sanitize_metadata(xmp)


                return {
                    "filename": os.path.basename(file_path),
                    "data_type": "common_image",
                    "format": img.format,
                    "source": file_path,
                    "shape": list(img_array.shape),
                    "size": img_array.size,
                    "dtype": str(img_array.dtype),
                    "ImageHeight": height,
                    "ImageWidth": width,
                    "mode": mode,
                    "color_space": self._get_color_space(img),
                    "has_alpha": mode == "RGBA",
                    "dpi": dpi,
                    "mean_color": self._get_mean_color(img_array),
                    "std_deviation": self._get_std_deviation(img_array),
                    "channels": channels,
                    "file_size": os.path.getsize(file_path),
                    "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                    "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "is_animated": getattr(img, "is_animated", False),
                    "frame_count": img.n_frames if getattr(img, "is_animated", False) else 1,
                    "metadata": {
                        "exif": safe_exif,
                        "iptc": safe_iptc,
                        "xmp": safe_xmp
                    },
                    "tags": ["standard", "raster"],
                    "thumbnail_base64": thumbnail_base64  # 更合理的命名
                }
        except Exception as e:
            return None

    def _get_mean_color(self, img_array: np.ndarray):
        if len(img_array.shape) == 3:
            return np.mean(img_array, axis=(0, 1)).tolist()
        else:
            return np.mean(img_array).tolist()

    def _get_std_deviation(self, img_array: np.ndarray):
        if len(img_array.shape) == 3:
            return np.std(img_array, axis=(0, 1)).tolist()
        else:
            return np.std(img_array).tolist()

    def _get_color_space(self, img: Image.Image):
        mode = img.mode
        color_spaces = {
            "RGB": "RGB",
            "RGBA": "RGBA",
            "L": "Grayscale",
            "CMYK": "CMYK",
            "YCbCr": "YCbCr",
            "HSV": "HSV",
            "LAB": "Lab"
        }
        return color_spaces.get(mode, mode)

class GeoTIFFParser(DataParser):
    """GeoTIFF 遥感图像解析器"""
    @staticmethod
    def supported_extensions():
        return [".tif", ".tiff"]

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            from osgeo import gdal
        except ImportError:
            raise ImportError("GDAL not installed. Please install via pip install GDAL or conda install -c conda-forge gdal")
        
        dataset = gdal.Open(file_path)
        if not dataset:
            return None

        band = dataset.GetRasterBand(1)
        metadata = dataset.GetMetadata()
        geotransform = dataset.GetGeoTransform()
        projection = dataset.GetProjection()
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        channels = dataset.RasterCount
        dtype = gdal.GetDataTypeName(band.DataType)
        
        with rasterio.open(file_path) as src:
            array = src.read(1)
        pil_img = Image.fromarray(array).convert('L').convert('RGB')

        pil_img.thumbnail((128, 128))
        img_byte_arr = BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        frame_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        return {
            "filename": os.path.basename(file_path),
            "data_type": "GeoTIFF",
            "format": os.path.splitext(file_path)[1].lower(),
            "source": file_path,
            "shape": [height, width, channels],
            "size": height * width * channels,
            "dtype": dtype,
            "ImageHeight": height,
            "ImageWidth": width,
            "mode": pil_img.mode,
            "color_space": self._get_color_space(pil_img),
            "has_alpha": pil_img.mode == "RGBA",
            "mean_color": self._get_mean_color(np.array(pil_img)),
            "std_deviation": self._get_std_deviation(np.array(pil_img)),
            "metadata": {
                "geo_geotransform": geotransform,
                "geo_projection": projection,
                "bands": dataset.RasterCount,
                "scale": band.GetScale() or 1.0,
                "offset": band.GetOffset() or 0.0
            },
            "pixel_resolution": [
                abs(geotransform[1]),
                abs(geotransform[5])
            ],
            "tags": ["geospatial", "satellite"],
            "first_frame_base64": frame_base64
        }

    def _get_color_space(self, img: Image.Image):
        mode = img.mode
        color_spaces = {
            "RGB": "RGB",
            "RGBA": "RGBA",
            "L": "Grayscale",
            "CMYK": "CMYK",
            "YCbCr": "YCbCr",
            "HSV": "HSV",
            "LAB": "Lab"
        }
        return color_spaces.get(mode, mode)

    def _get_mean_color(self, img_array: np.ndarray):
        if len(img_array.shape) == 3:
            return np.mean(img_array, axis=(0, 1)).tolist()
        else:
            return np.mean(img_array).tolist()

    def _get_std_deviation(self, img_array: np.ndarray):
        if len(img_array.shape) == 3:
            return np.std(img_array, axis=(0, 1)).tolist()
        else:
            return np.std(img_array).tolist()

class EnviERDASParser(DataParser):
    """Envi / ERDAS 图像解析器"""
    @staticmethod
    def supported_extensions():
        return [".envi", ".hdr", ".raw", ".img"]  # Envi 文件通常以 .hdr + .raw 形式存在

    def parse(self, file_path: str) -> Dict[str, Any]:
        import rasterio
        with rasterio.open(file_path) as src:
            width = src.width
            height = src.height
            count = src.count
            dtype = str(src.dtypes[0])
            crs = None if src.crs is None else src.crs.to_string()
            transform = src.transform
            metadata = src.tags()
            img_array = src.read()

        mean_color = np.mean(img_array, axis=(1, 2)).tolist()
        std_deviation = np.std(img_array, axis=(1, 2)).tolist()

        return {
            "filename": os.path.basename(file_path),
            "data_type": "Envi/ERDAS",
            "format": os.path.splitext(file_path)[1].lower(),
            "source": file_path,
            "shape": list(img_array.shape),
            "size": img_array.size,
            "dtype": dtype,
            "ImageHeight": height,
            "ImageWidth": width,
            "mode": "unknown",
            "color_space": "unknown",
            "has_alpha": count == 4,
            "mean_color": mean_color,
            "std_deviation": std_deviation,
            "channels": count,
            "file_size": os.path.getsize(file_path),
            "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "metadata": {
                "crs": crs,
                "transform": transform,
                "tags": metadata
            },
            "tags": ["geospatial", "remote_sensing"],
            "first_frame_base64": None  # Envi/ERDAS 一般不直接支持 Base64 缩略图
        }
        