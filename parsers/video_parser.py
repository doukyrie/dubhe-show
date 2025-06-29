import os
import numpy as np
import base64
from PIL import Image
import json
import cv2
import os
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from core import DataParser

class CommonVideoParser(DataParser):

    @staticmethod
    def supported_extensions():
        return ['.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.ts', '.m4v']

    def parse(self, file_path: str) -> Dict[str, Any]:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video file: {file_path}")

        # 获取基本属性
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        cap.release()

        # 使用 OpenCV 读取首帧用于生成 Base64 缩略图
        first_frame = self._get_first_frame(file_path)

        # 构建返回的字典
        return {
            "filename": os.path.basename(file_path),
            "data_type": "video",
            "format": os.path.splitext(file_path)[1][1:].upper(),
            "source": file_path,
            "shape": [height, width, 3],  # 假设 RGB 图像
            "size": height * width * 3 * total_frames,
            "dtype": "uint8",
            "ImageHeight": height,
            "ImageWidth": width,
            "mode": "RGB",
            "channels": 3,
            "duration": round(total_frames / frame_rate, 2) if frame_rate > 0 else 0,
            "frame_rate": frame_rate,
            "total_frames": total_frames,
            "mean_color": self._get_mean_color(first_frame),
            "std_deviation": self._get_std_deviation(first_frame),
            "max_value": int(np.max(first_frame)),
            "min_value": int(np.min(first_frame)),
            "file_size": os.path.getsize(file_path),
            "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "metadata": self._extract_metadata(file_path),  # 可结合 FFmpeg 扩展
            "tags": ["video"],
            "first_frame_base64": self._to_base64(first_frame)
        }

    def _get_first_frame(self, file_path: str) -> np.ndarray:
        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise ValueError(f"无法读取视频首帧: {file_path}")
        return frame  # BGR -> 后续可转为 RGB

    def _to_base64(self, frame: np.ndarray) -> str:
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img.thumbnail((128, 128))
        byte_io = BytesIO()
        img.save(byte_io, format="JPEG")
        return base64.b64encode(byte_io.getvalue()).decode("utf-8")

    def _get_mean_color(self, frame: np.ndarray) -> list:
        return np.mean(frame, axis=(0, 1)).tolist()

    def _get_std_deviation(self, frame: np.ndarray) -> list:
        return np.std(frame, axis=(0, 1)).tolist()

    def _extract_metadata(self, file_path: str) -> dict:
        """预留方法，后续可集成 FFmpeg 提取详细元数据"""
        return {
            "opencv_parsed": True
        }