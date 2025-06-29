import scipy.io
import zipfile
import os
import shutil
import scipy.io
import json
import numpy as np
def inspect_mat_file(file_path):
    """
    查看.mat文件中的所有属性
    
    参数:
        file_path (str): .mat文件的路径
        
    返回:
        dict: 包含文件元数据和变量信息的字典
    """
    try:
        # 加载MAT文件
        data = scipy.io.loadmat(file_path)
        
        # 提取变量名（过滤掉MATLAB系统变量）
        variables = [key for key in data.keys() if not key.startswith('__')]
        
        # 收集变量详细信息
        var_info = {}
        for var in variables:
            value = data[var]
            var_info[var] = {
                "type": str(type(value)),
                "shape": value.shape if hasattr(value, 'shape') else None,
                "dtype": str(value.dtype) if hasattr(value, 'dtype') else None,
                "size": value.size if hasattr(value, 'size') else None,
                "is_complex": np.iscomplexobj(value) if hasattr(value, 'dtype') else False,
                "sample_value": _get_sample_value(value)
            }
        
        # 返回结果
        return {
            "file_path": file_path,
            "file_size": f"{os.path.getsize(file_path)/1024:.2f} KB",
            "variables": variables,
            "variable_details": var_info,
            "system_variables": [key for key in data.keys() if key.startswith('__')]
        }
    
    except Exception as e:
        return {"error": str(e)}

def _get_sample_value(value):
    """获取变量的示例值"""
    try:
        # 处理数组
        if isinstance(value, np.ndarray):
            if value.size == 0:
                return "empty array"
            elif value.size == 1:
                return value.item()
            else:
                # 返回前3个元素（如果是一维）或形状（如果是多维）
                if value.ndim == 1:
                    return value[:3].tolist()
                else:
                    return f"array of shape {value.shape}"
        
        # 处理其他类型
        return value
    
    except:
        return "unable to extract sample"

if __name__ == "__main__":
    # 示例用法
    file_path = "data1\F16_hrrp_theta_75_phi_0.1.mat"  # 替换为你的.mat文件路径
    result = inspect_mat_file(file_path)
    
    # 格式化输出结果
    print(f"文件信息: {result['file_path']} ({result['file_size']})")
    print("\n变量列表:")
    for var in result["variables"]:
        print(f"  - {var}")
    
    print("\n变量详细信息:")
    for var, info in result["variable_details"].items():
        print(f"变量名: {var}")
        print(f"  类型: {info['type']}")
        print(f"  形状: {info['shape']}")
        print(f"  数据类型: {info['dtype']}")
        print(f"  大小: {info['size']}")
        print(f"  是否复数: {info['is_complex']}")
        print(f"  示例值: {info['sample_value']}")
        print()
    
    print(f"\n系统变量: {result['system_variables']}")