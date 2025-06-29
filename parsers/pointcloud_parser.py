import numpy as np
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import BytesIO
import base64
from PIL import Image
from core import DataParser

class PCDParser(DataParser):

    @staticmethod
    def supported_extensions():
        return ['.pcd']

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            # 使用开源库（如 open3d）读取PCD文件
            import open3d as o3d
            pcd = o3d.io.read_point_cloud(file_path)
            
            # 获取点云属性
            points = np.asarray(pcd.points)
            colors = np.asarray(pcd.colors) if pcd.has_colors() else None
            normals = np.asarray(pcd.normals) if pcd.has_normals() else None

            # 生成点云缩略图（俯视图）
            thumbnail_base64 = self._generate_thumbnail(points, colors)

            return {
                "filename": os.path.basename(file_path),
                "data_type": "point_cloud",
                "format": "PCD",
                "source": file_path,
                "point_count": len(points),
                "has_colors": pcd.has_colors(),
                "has_normals": pcd.has_normals(),
                "bounding_box": self._calculate_bounding_box(points),
                "mean_intensity": self._get_mean_intensity(pcd),
                "density": self._calculate_density(points, file_path),
                "metadata": self._extract_pcd_metadata(file_path),
                "file_size": os.path.getsize(file_path),
                "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "tags": ["3d", "point_cloud"],
                "thumbnail_base64": thumbnail_base64,
                "attributes": {
                    "points": points.shape[1] if points.ndim == 2 else 3,
                    "colors": 3 if colors is not None else 0,
                    "normals": 3 if normals is not None else 0
                }
            }
        except Exception as e:
            return None

    def _calculate_bounding_box(self, points: np.ndarray) -> Dict[str, List[float]]:
        """计算点云包围盒"""
        return {
            "min": np.min(points, axis=0).tolist(),
            "max": np.max(points, axis=0).tolist(),
            "center": np.mean(points, axis=0).tolist()
        }

    def _calculate_density(self, points: np.ndarray, file_path: str) -> float:
        """估算点云密度（点/立方米）"""
        bbox = self._calculate_bounding_box(points)
        volume = np.prod(np.array(bbox["max"]) - np.array(bbox["min"]))
        return len(points) / max(volume, 1e-6)  # 避免除以零

    def _get_mean_intensity(self, pcd) -> float:
        """获取平均强度（如果存在强度通道）"""
        if hasattr(pcd, 'intensity'):
            return float(np.mean(pcd.intensity))
        return 0.0

    def _extract_pcd_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取PCD文件头中的元数据"""
        metadata = {}
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                if line.startswith('FIELDS'):
                    metadata['fields'] = line.split()[1:]
                elif line.startswith('SIZE'):
                    metadata['sizes'] = list(map(int, line.split()[1:]))
                elif line.startswith('TYPE'):
                    metadata['types'] = line.split()[1:]
                elif line.startswith('COUNT'):
                    metadata['counts'] = list(map(int, line.split()[1:]))
                elif line.startswith('WIDTH'):
                    metadata['width'] = int(line.split()[1])
                elif line.startswith('HEIGHT'):
                    metadata['height'] = int(line.split()[1])
                elif line.startswith('VIEWPOINT'):
                    metadata['viewpoint'] = list(map(float, line.split()[1:]))
                elif line.startswith('POINTS'):
                    metadata['points'] = int(line.split()[1])
                elif line.startswith('DATA'):
                    metadata['data_format'] = line.split()[1]
                    break
        return metadata

    def _generate_thumbnail(self, points: np.ndarray, colors: np.ndarray = None) -> str:
        """生成点云俯视图缩略图"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            
            fig = plt.figure(figsize=(2, 2), dpi=72)
            ax = fig.add_subplot(111)
            
            # 仅使用XY平面投影
            x, y = points[:, 0], points[:, 1]
            if colors is not None:
                ax.scatter(x, y, c=colors, s=0.1, marker='.')
            else:
                ax.scatter(x, y, s=0.1, c='blue', marker='.')
            
            ax.axis('off')
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            
            # 转换为PIL图像并编码为Base64
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except:
            return ""

class E57Parser(DataParser):

    @staticmethod
    def supported_extensions():
        return ['.e57']

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            # 使用pye57库读取E57文件
            import pye57
            e57 = pye57.E57(file_path)
            
            # 获取扫描数量和点云数据
            scan_count = e57.scan_count
            header = e57.get_header(0)
            point_count = header.point_count
            
            # 读取部分点云数据（避免内存问题）
            points = e57.read_scan(0, intensity=True, colors=True, normals=True, row_limit=10000)
            
            return {
                "filename": os.path.basename(file_path),
                "data_type": "point_cloud",
                "format": "E57",
                "source": file_path,
                "scan_count": scan_count,
                "point_count": point_count,
                "has_colors": "rgb" in points.dtype.names,
                "has_normals": "normals" in points.dtype.names,
                "has_intensity": "intensity" in points.dtype.names,
                "bounding_box": self._calculate_e57_bounding_box(e57),
                "metadata": self._extract_e57_metadata(e57),
                "file_size": os.path.getsize(file_path),
                "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "tags": ["3d", "lidar", "e57"],
                "coordinate_system": header.pose.rotation,  # 坐标系信息
                "attributes": {
                    "available_fields": list(points.dtype.names)
                }
            }
        except Exception as e:
            return None

    def _calculate_e57_bounding_box(self, e57) -> Dict[str, List[float]]:
        """计算E57文件的整体包围盒"""
        import pye57
        bounds = {
            "x_min": float('inf'),
            "y_min": float('inf'),
            "z_min": float('inf'),
            "x_max": -float('inf'),
            "y_max": -float('inf'),
            "z_max": -float('inf')
        }
        
        for i in range(e57.scan_count):
            header = e57.get_header(i)
            bounds["x_min"] = min(bounds["x_min"], header.x_min)
            bounds["y_min"] = min(bounds["y_min"], header.y_min)
            bounds["z_min"] = min(bounds["z_min"], header.z_min)
            bounds["x_max"] = max(bounds["x_max"], header.x_max)
            bounds["y_max"] = max(bounds["y_max"], header.y_max)
            bounds["z_max"] = max(bounds["z_max"], header.z_max)
        
        return {
            "min": [bounds["x_min"], bounds["y_min"], bounds["z_min"]],
            "max": [bounds["x_max"], bounds["y_max"], bounds["z_max"]],
            "center": [
                (bounds["x_min"] + bounds["x_max"]) / 2,
                (bounds["y_min"] + bounds["y_max"]) / 2,
                (bounds["z_min"] + bounds["z_max"]) / 2
            ]
        }

    def _extract_e57_metadata(self, e57) -> Dict[str, Any]:
        """提取E57文件的元数据"""
        metadata = {}
        scan_metadata = []
        
        for i in range(e57.scan_count):
            header = e57.get_header(i)
            scan_metadata.append({
                "guid": header.guid,
                "name": header.name,
                "description": header.description,
                "sensor_vendor": header.sensor_vendor,
                "sensor_model": header.sensor_model,
                "sensor_serial": header.sensor_serial,
                "acquisition_date": header.acquisition_date,
                "temperature": header.temperature,
                "relative_humidity": header.relative_humidity,
                "point_count": header.point_count
            })
        
        metadata["scans"] = scan_metadata
        return metadata

class LasLazParser(DataParser):

    @staticmethod
    def supported_extensions():
        return ['.las', '.laz']

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            # 使用laspy库读取LAS/LAZ文件
            import laspy
            las = laspy.read(file_path)
            
            # 获取点云属性
            point_format = las.point_format
            has_rgb = hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue')
            has_intensity = hasattr(las, 'intensity')
            
            return {
                "filename": os.path.basename(file_path),
                "data_type": "point_cloud",
                "format": "LAZ" if file_path.lower().endswith('.laz') else "LAS",
                "source": file_path,
                "point_count": len(las.points),
                "point_format": point_format.id,
                "has_colors": has_rgb,
                "has_intensity": has_intensity,
                "has_classification": hasattr(las, 'classification'),
                "bounding_box": self._calculate_las_bounding_box(las),
                "metadata": self._extract_las_metadata(las),
                "file_size": os.path.getsize(file_path),
                "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "tags": ["3d", "lidar", "las"],
                "coordinate_system": {
                    "epsg": las.header.parse_crs().to_epsg() if las.header.parse_crs() else None
                },
                "attributes": {
                    "available_fields": list(point_format.dimension_names)
                }
            }
        except Exception as e:
            return None

    def _calculate_las_bounding_box(self, las) -> Dict[str, List[float]]:
        """计算LAS文件的包围盒"""
        return {
            "min": [las.header.min[0], las.header.min[1], las.header.min[2]],
            "max": [las.header.max[0], las.header.max[1], las.header.max[2]],
            "center": [
                (las.header.min[0] + las.header.max[0]) / 2,
                (las.header.min[1] + las.header.max[1]) / 2,
                (las.header.min[2] + las.header.max[2]) / 2
            ]
        }

    def _extract_las_metadata(self, las) -> Dict[str, Any]:
        """提取LAS文件的元数据"""
        header = las.header
        return {
            "version": f"{header.major_version}.{header.minor_version}",
            "point_data_format": header.point_format.id,
            "scale": [header.scales[0], header.scales[1], header.scales[2]],
            "offset": [header.offsets[0], header.offsets[1], header.offsets[2]],
            "system_identifier": header.system_identifier,
            "generating_software": header.generating_software,
            "file_creation": {
                "day": header.file_creation.day,
                "year": header.file_creation.year
            },
            "point_count_by_return": header.point_count_by_return.tolist()
        }