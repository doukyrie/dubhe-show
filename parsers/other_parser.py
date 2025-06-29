import os
import json
from core import DataParser
from typing import Dict, Any, List, Optional
from io import BytesIO
import base64
from datetime import datetime
import numpy as np
from PIL import Image

class NMEAParser(DataParser):
    """
    解析NMEA 0183格式的GPS/GNSS数据
    支持GGA, RMC, GSA, GSV等常见语句
    """
    
    @staticmethod
    def supported_extensions():
        return ['.nmea', '.txt', '.log']

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # 解析所有NMEA语句
            parsed_data = {
                "gga": [],
                "rmc": [],
                "gsa": [],
                "gsv": [],
                "other": []
            }
            
            for line in lines:
                line = line.strip()
                if not line.startswith('$'):
                    continue
                
                # 分离语句类型和数据
                sentence_type = line[3:6].upper()
                data = self._parse_nmea_line(line)
                
                if sentence_type == "GGA":
                    parsed_data["gga"].append(data)
                elif sentence_type == "RMC":
                    parsed_data["rmc"].append(data)
                elif sentence_type == "GSA":
                    parsed_data["gsa"].append(data)
                elif sentence_type == "GSV":
                    parsed_data["gsv"].append(data)
                else:
                    parsed_data["other"].append({
                        "type": sentence_type,
                        "raw": line
                    })
            
            # 提取关键统计信息
            stats = self._calculate_nmea_stats(parsed_data)
            
            return {
                "filename": os.path.basename(file_path),
                "data_type": "nmea",
                "format": "NMEA 0183",
                "source": file_path,
                "sentence_counts": {
                    "GGA": len(parsed_data["gga"]),
                    "RMC": len(parsed_data["rmc"]),
                    "GSA": len(parsed_data["gsa"]),
                    "GSV": len(parsed_data["gsv"]),
                    "OTHER": len(parsed_data["other"])
                },
                "time_range": stats["time_range"],
                "position_stats": stats["position_stats"],
                "altitude_stats": stats["altitude_stats"],
                "satellite_stats": stats["satellite_stats"],
                "file_size": os.path.getsize(file_path),
                "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "tags": ["gps", "geospatial"],
                "metadata": {
                    "coordinate_system": "WGS84",
                    "contains_gnss_data": len(parsed_data["gga"]) > 0
                },
                "sample_data": self._get_nmea_samples(parsed_data)
            }
        except Exception as e:
            return None

    def _parse_nmea_line(self, line: str) -> Dict[str, Any]:
        """解析单条NMEA语句"""
        parts = line.split(',')
        sentence_type = parts[0][3:6]
        
        # GGA - GPS定位数据
        if sentence_type == "GGA":
            return {
                "time": parts[1],
                "latitude": self._nmea_to_decimal(parts[2], parts[3]),
                "longitude": self._nmea_to_decimal(parts[4], parts[5]),
                "quality": int(parts[6]) if parts[6] else None,
                "satellites": int(parts[7]) if parts[7] else None,
                "hdop": float(parts[8]) if parts[8] else None,
                "altitude": float(parts[9]) if parts[9] else None,
                "geoid_separation": float(parts[11]) if parts[11] else None,
                "raw": line
            }
        
        # RMC - 推荐最小定位信息
        elif sentence_type == "RMC":
            return {
                "time": parts[1],
                "status": parts[2],
                "latitude": self._nmea_to_decimal(parts[3], parts[4]),
                "longitude": self._nmea_to_decimal(parts[5], parts[6]),
                "speed_knots": float(parts[7]) if parts[7] else None,
                "true_course": float(parts[8]) if parts[8] else None,
                "date": parts[9],
                "raw": line
            }
        
        # 其他语句保留原始数据
        return {
            "type": sentence_type,
            "raw": line
        }

    def _nmea_to_decimal(self, value: str, direction: str) -> float:
        """NMEA格式坐标转十进制"""
        if not value or not direction:
            return None
        degrees = float(value[:2]) if len(value) > 2 else 0.0
        minutes = float(value[2:])
        decimal = degrees + minutes / 60.0
        if direction in ['S', 'W']:
            decimal *= -1
        return decimal

    def _calculate_nmea_stats(self, data: Dict[str, List]) -> Dict[str, Any]:
        """计算NMEA数据的统计信息"""
        stats = {
            "time_range": {"start": None, "end": None},
            "position_stats": {
                "latitude": {"min": None, "max": None, "mean": None},
                "longitude": {"min": None, "max": None, "mean": None}
            },
            "altitude_stats": {"min": None, "max": None, "mean": None},
            "satellite_stats": {"min": None, "max": None, "mean": None}
        }
        
        # 提取所有GGA数据的时间、位置、高度
        times = []
        lats = []
        lons = []
        alts = []
        sats = []
        
        for gga in data["gga"]:
            if gga.get("time"):
                times.append(gga["time"])
            if gga.get("latitude") is not None:
                lats.append(gga["latitude"])
            if gga.get("longitude") is not None:
                lons.append(gga["longitude"])
            if gga.get("altitude") is not None:
                alts.append(gga["altitude"])
            if gga.get("satellites") is not None:
                sats.append(gga["satellites"])
        
        # 计算统计值
        if times:
            stats["time_range"]["start"] = min(times)
            stats["time_range"]["end"] = max(times)
        
        if lats:
            stats["position_stats"]["latitude"] = {
                "min": min(lats),
                "max": max(lats),
                "mean": sum(lats) / len(lats)
            }
        
        if lons:
            stats["position_stats"]["longitude"] = {
                "min": min(lons),
                "max": max(lons),
                "mean": sum(lons) / len(lons)
            }
        
        if alts:
            stats["altitude_stats"] = {
                "min": min(alts),
                "max": max(alts),
                "mean": sum(alts) / len(alts)
            }
        
        if sats:
            stats["satellite_stats"] = {
                "min": min(sats),
                "max": max(sats),
                "mean": sum(sats) / len(sats)
            }
        
        return stats

    def _get_nmea_samples(self, data: Dict[str, List]) -> Dict[str, Any]:
        """获取各类NMEA语句的样例"""
        samples = {}
        for key in data:
            if data[key]:
                samples[key] = data[key][0]
                if len(data[key]) > 1:
                    samples[key]["_more"] = f"+{len(data[key])-1} more records"
        return samples
    
class VTKParser(DataParser):
    """
    解析VTK格式的可视化数据（.vtk）
    支持结构化网格和非结构化网格
    """
    
    @staticmethod
    def supported_extensions():
        return ['.vtk']

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            # 使用pyvista库读取VTK文件
            import pyvista as pv
            mesh = pv.read(file_path)
            
            # 生成缩略图
            thumbnail_base64 = self._generate_vtk_thumbnail(mesh)
            
            # 获取网格属性
            bounds = mesh.bounds
            center = mesh.center
            n_cells = mesh.n_cells
            n_points = mesh.n_points
            
            # 检查数据类型
            is_structured = isinstance(mesh, (pv.StructuredGrid, pv.RectilinearGrid, pv.UniformGrid))
            is_poly = isinstance(mesh, pv.PolyData)
            
            # 获取标量和向量场信息
            point_data = self._extract_field_info(mesh.point_data)
            cell_data = self._extract_field_info(mesh.cell_data)
            
            return {
                "filename": os.path.basename(file_path),
                "data_type": "vtk_mesh",
                "format": "VTK",
                "source": file_path,
                "mesh_type": self._get_mesh_type(mesh),
                "is_structured": is_structured,
                "is_poly": is_poly,
                "bounds": {
                    "x": [bounds[0], bounds[1]],
                    "y": [bounds[2], bounds[3]],
                    "z": [bounds[4], bounds[5]]
                },
                "center": center,
                "n_points": n_points,
                "n_cells": n_cells,
                "point_data_fields": point_data,
                "cell_data_fields": cell_data,
                "file_size": os.path.getsize(file_path),
                "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "tags": ["3d", "visualization", "mesh"],
                "thumbnail_base64": thumbnail_base64,
                "metadata": {
                    "vtk_version": "5.1",  # 可从文件头解析
                    "byte_order": "LittleEndian"  # 假设
                }
            }
        except Exception as e:
            return None

    def _get_mesh_type(self, mesh) -> str:
        """获取VTK网格类型"""
        import pyvista as pv
        if isinstance(mesh, pv.UniformGrid):
            return "UniformGrid"
        elif isinstance(mesh, pv.RectilinearGrid):
            return "RectilinearGrid"
        elif isinstance(mesh, pv.StructuredGrid):
            return "StructuredGrid"
        elif isinstance(mesh, pv.PolyData):
            return "PolyData"
        elif isinstance(mesh, pv.UnstructuredGrid):
            return "UnstructuredGrid"
        else:
            return "Unknown"

    def _extract_field_info(self, field_data) -> List[Dict[str, Any]]:
        """提取点数据或单元数据的字段信息"""
        fields = []
        for name in field_data:
            arr = field_data[name]
            fields.append({
                "name": name,
                "type": str(arr.dtype),
                "components": arr.shape[1] if len(arr.shape) > 1 else 1,
                "range": [float(np.min(arr)), float(np.max(arr))] if arr.size > 0 else None
            })
        return fields

    def _generate_vtk_thumbnail(self, mesh) -> str:
        """生成VTK数据的缩略图"""
        try:
            import pyvista as pv
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            
            # 创建简单绘图
            plotter = pv.Plotter(off_screen=True, window_size=[256, 256])
            plotter.add_mesh(mesh, show_edges=True, color="tan")
            plotter.view_isometric()
            image = plotter.screenshot(None, return_img=True)
            plotter.close()
            
            # 转换为PIL图像
            img = Image.fromarray(image)
            img.thumbnail((128, 128))
            
            # 编码为Base64
            buf = BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except:
            return ""