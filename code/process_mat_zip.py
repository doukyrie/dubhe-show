import zipfile
import os
import shutil
import scipy.io
import json
import numpy as np

from mysql_1 import insert_dataset_n, select_data_standard_attr
from datetime import datetime

from mysql_datasetfile import insert_data_file_n


def process_mat_zip(datasetname,zip_path,group_id):
    # 检查ZIP文件是否存在
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(f"ZIP文件不存在: {zip_path}")
    
    # 创建解压目录路径（移除.zip后缀）
    extract_dir = os.path.splitext(zip_path)[0]
    
    # 创建临时解压目录
    temp_extract_dir = extract_dir + "_temp"
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    # 解压ZIP文件到临时目录
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)
    
    # 检查解压后的目录结构
    extracted_items = os.listdir(temp_extract_dir)
    
    # 如果只有一个子目录，且该目录名与目标目录名相同
    if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_dir, extracted_items[0])):
        inner_dir = os.path.join(temp_extract_dir, extracted_items[0])
        
        # 如果内部目录名与目标目录名相同，则直接移动内容
        if os.path.basename(inner_dir) == os.path.basename(extract_dir):
            # 创建目标目录
            os.makedirs(extract_dir, exist_ok=True)
            
            # 移动所有内容到目标目录
            for item in os.listdir(inner_dir):
                src = os.path.join(inner_dir, item)
                dst = os.path.join(extract_dir, item)
                shutil.move(src, dst)
            
            # 删除空目录
            shutil.rmtree(inner_dir)
        else:
            # 重命名整个目录
            shutil.move(inner_dir, extract_dir)
    else:
        # 直接重命名整个目录
        shutil.move(temp_extract_dir, extract_dir)
    
    # 清理临时目录（如果存在）
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    
    # 收集所有文件并分类
    total_files = 0
    non_mat_files = []  # 存储非MAT文件的文件名
    mat_files = []      # 存储MAT文件的完整路径
    
    # 遍历目录并分类文件
    for root, _, files in os.walk(extract_dir):
        for file in files:
            total_files += 1
            if file.endswith('.mat'):
                mat_files.append(os.path.join(root, file))
            else:
                non_mat_files.append(file)  # 只记录文件名
    
    # 生成非MAT文件JSON
    base_name = os.path.basename(extract_dir)
    fail_json_file = f"{base_name}-fail.json"
    fail_json_path = os.path.abspath(os.path.join(os.path.dirname(extract_dir), fail_json_file))
    
    # 构建非MAT文件列表
    non_mat_data = [{"filename": filename} for filename in non_mat_files]
    
    # 保存非MAT文件JSON
    with open(fail_json_path, 'w', encoding='utf-8') as f:
        json.dump(non_mat_data, f, indent=2, ensure_ascii=False)
    
    # 解析每个MAT文件
    result = []
    required_vars = select_data_standard_attr(1)
    success_count = 0  # 成功处理的MAT文件计数器
    
    # 自定义JSON序列化器，处理复数和numpy类型
    class ComplexEncoder(json.JSONEncoder):
        def default(self, obj):
            # 处理复数类型
            if isinstance(obj, complex):
                return {"real": obj.real, "imag": obj.imag}
            
            # 处理numpy标量
            if isinstance(obj, np.generic):
                return obj.item()
            
            # 处理numpy数组
            if isinstance(obj, np.ndarray):
                # 复数数组特殊处理
                if np.iscomplexobj(obj):
                    return {
                        "real": obj.real.tolist(),
                        "imag": obj.imag.tolist()
                    }
                return obj.tolist()
            
            # 其他类型使用默认处理
            return super().default(obj)
    
    # 处理MAT文件
    for mat_file in mat_files:
        try:
            data = scipy.io.loadmat(mat_file)
            success_count += 1  # 增加成功计数器
            
            file_data = {"filename": os.path.basename(mat_file)}
            
            for var in required_vars:
                if var in data:
                    file_data[var] = data[var]
                else:
                    file_data[var] = None
            
            result.append(file_data)
        except Exception as e:
            print(f"加载MAT文件失败 {mat_file}: {e}")
            # 将加载失败的MAT文件也记录到非MAT文件中
            non_mat_files.append(os.path.basename(mat_file))
    
    # 生成输出JSON文件名
    json_file = base_name + ".json"
    json_path = os.path.abspath(os.path.join(os.path.dirname(extract_dir), json_file))
    
    # 保存JSON文件，使用自定义编码器
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, cls=ComplexEncoder)
    
    # 更新非MAT文件JSON（包含加载失败的MAT文件）
    non_mat_data = [{"filename": filename} for filename in non_mat_files]
    with open(fail_json_path, 'w', encoding='utf-8') as f:
        json.dump(non_mat_data, f, indent=2, ensure_ascii=False)
    

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')  # 包含毫秒
    print(now)  # 输出类似：2025-04-05 14:30:45.123456
    # 打印处理统计信息
    print(f"总文件数量: {total_files}")
    print(f"非MAT文件数量: {len(non_mat_files)}")
    print(f"MAT文件数量: {len(mat_files)}")
    print(f"成功处理的MAT文件数量: {success_count}")
    print(f"失败处理的MAT文件数量: {len(mat_files) - success_count}")
    print(f"成功生成JSON文件: {json_path}")
    print(f"成功生成非MAT文件列表: {fail_json_path}")
    zip_filename = os.path.basename(zip_path)  # 获取文件名，如 data1.zip
    zip_abs_path = os.path.abspath(zip_path)   # 获取绝对路径

    dataset_id = insert_dataset_n(datasetname,1,os.path.abspath(extract_dir),json_path,fail_json_path,'admin',now,now,2,success_count,total_files,zip_filename,'',group_id)
    print(dataset_id)

    # 默认值
    status = 0
    create_user_id = "admin"

    # 支持的扩展名列表（小写），未来可扩展
    allowed_extensions = ['.mat']

    # 遍历目录中的所有文件
    for filename in os.listdir(extract_dir):
        file_path = os.path.join(extract_dir, filename)
        
        # 确保是文件而不是子目录
        if os.path.isfile(file_path):
            name = filename
            _, ext = os.path.splitext(filename)

            # 过滤：只处理允许的扩展名
            if ext.lower() not in allowed_extensions:
                print(f"跳过不支持的文件: {filename}（扩展名不在白名单中）")
                continue

            file_url = os.path.abspath(file_path)   # 文件绝对路径
            file_type = ext[1:].lower()             # 去掉点号的后缀，如 'mat'
            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 当前时间
            
            # 调用插入函数
            insert_data_file_n(name, status, dataset_id, file_url, create_user_id, create_time, file_type)
    # 返回两个JSON文件的绝对路径
    return json_path, fail_json_path


if __name__ == '__main__':
    process_mat_zip('testt','data1.zip')