import datetime
from mysql.connector import pooling
from pymysql import Error
import os
import shutil
import mysql.connector
from datetime import datetime

connection_pool = pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    host='192.168.3.37',
    port=3306,
    user='root',
    password='123456',
    database='dubhe-prod'
)
import os

def clear_files_in_folder(folder_path):
    """
    清空指定文件夹中的所有文件，但保留子文件夹及其内容。
    
    参数:
    folder_path (str): 要清理的文件夹路径
    """
    if not os.path.isdir(folder_path):
        print(f"路径 {folder_path} 不是一个有效的文件夹。")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        # 如果是文件，则删除
        if os.path.isfile(item_path):
            try:
                os.remove(item_path)
                print(f"已删除文件: {item_path}")
            except Exception as e:
                print(f"无法删除文件 {item_path}: {e}")


#def parse_query_params_datasetfile(res):
import json

import json
import os
import shutil
import mysql.connector
from datetime import datetime

import os
import shutil
import mysql.connector
from datetime import datetime

def make_dataset(request_data, result):
    # 1. 解析前端请求数据
    name = request_data['new_dataset_name']
    group_id = request_data['group_id']
    dataset_ids = request_data.get('dataset_id', [])
    labels = request_data.get('labels', [])
    desc = request_data['desc']

    # 2. 创建目录
    base_path = r'C:\Users\admin\Desktop\flask\uploads'
    new_dir_path = os.path.join(base_path, name)
    os.makedirs(new_dir_path, exist_ok=True)
    
    try:
        # 3. 连接数据库
        conn = mysql.connector.connect(
            host="192.168.3.37",
            port = 3306,
            user="root",
            password="123456",
            database="dubhe-prod"
        )
        cursor = conn.cursor()

        # 4. 获取任意dataset_id对应的data_type
        if result and dataset_ids:
            dataset_id_to_query = result[0]['dataset_id']
        elif dataset_ids:
            dataset_id_to_query = dataset_ids[0]
        else:
            dataset_id_to_query = None

        if dataset_id_to_query:
            cursor.execute(
                "SELECT data_type FROM data_dataset_n WHERE id = %s",
                (dataset_id_to_query,)
            )
            data_type_row = cursor.fetchone()
            data_type = data_type_row[0] if data_type_row else 'default_type'
        else:
            data_type = 'default_type'

        # 5. 计算数据大小
        data_size = len(result)

        # 6. 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 7. 插入新数据集记录
        insert_dataset_query = """
        INSERT INTO data_dataset_n (
            name, data_type, uri, create_user_id, 
            create_time, update_time, status, 
            data_size, data_src_size, group_id,remark
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        dataset_values = (
            name,
            data_type,
            new_dir_path.replace('\\', '/'),
            'admin',
            current_time,
            current_time,
            2,
            data_size,
            data_size,
            group_id,
            desc
        )

        cursor.execute(insert_dataset_query, dataset_values)
        conn.commit()

        # 8. 获取新数据集的ID
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_dataset_id = cursor.fetchone()[0]
        
        # 9. 遍历并处理每个文件
        for item in result:
            source_file = item['file_url']
            # 处理路径格式
            source_file = source_file.replace('\\\\', '\\')
            
            # 只处理文件
            if os.path.isfile(source_file):
                # 获取文件名和后缀
                filename = os.path.basename(source_file)
                file_base, file_ext = os.path.splitext(filename)
                file_type = file_ext[1:] if file_ext else ''  # 去掉点号
                
                # 目标路径
                dest_path = os.path.join(new_dir_path, filename)
                
                try:
                    # 复制文件到根目录
                    shutil.copy2(source_file, dest_path)
                    print(f"成功复制到根目录: {source_file} -> {dest_path}")
                    
                    # 处理标签子目录
                    label_list = []
                    # 获取第四个标签数组（索引3）
                    if len(item.get('label_names', [])) > 3:
                        label_list = item['label_names'][3]
                    
                    # 过滤空标签
                    valid_labels = [label for label in label_list if label and label.strip()]
                    
                    # 为每个有效标签创建子目录并复制文件
                    for label in valid_labels:
                        # 清理标签名称，移除非法字符
                        clean_label = ''.join(c for c in label if c.isalnum() or c in ['_', '-', ' '])
                        clean_label = clean_label.strip()
                        
                        if not clean_label:
                            continue
                            
                        # 创建标签子目录
                        label_dir = os.path.join(new_dir_path, clean_label)
                        os.makedirs(label_dir, exist_ok=True)
                        
                        # 标签目录中的目标路径
                        label_dest_path = os.path.join(label_dir, filename)
                        
                        # 复制文件到标签目录
                        shutil.copy2(source_file, label_dest_path)
                        print(f"成功复制到标签目录 '{clean_label}': {source_file} -> {label_dest_path}")
                    # 示例调用：

                    clear_files_in_folder(new_dir_path)
                    # 获取当前时间
                    file_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 插入文件记录
                    insert_file_query = """
                    INSERT INTO data_file_n (
                        name, status, dataset_id, file_url, 
                        create_user_id, create_time, file_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    file_values = (
                        file_base,  # 不带后缀的文件名
                        1,          # status=1
                        new_dataset_id,
                        dest_path.replace('\\', '/'),
                        'admin',
                        file_time,
                        file_type
                    )
                    
                    cursor.execute(insert_file_query, file_values)
                    conn.commit()
                    
                    # 获取新文件ID
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    newfile_id = cursor.fetchone()[0]
                    
                    # 获取原始文件ID和数据集ID
                    original_file_id = item['id']
                    original_dataset_id = item['dataset_id']
                    
                    # 查询标签关系
                    query_label_query = """
                    SELECT label_id 
                    FROM file_label_rela 
                    WHERE file_id = %s AND dataset_id = %s AND group_id = %s
                    """
                    cursor.execute(query_label_query, 
                                  (original_file_id, original_dataset_id, group_id))
                    label_ids = [row[0] for row in cursor.fetchall()]
                    
                    # 插入新标签关系
                    if label_ids:
                        insert_label_query = """
                        INSERT INTO file_label_rela 
                            (file_id, label_id, group_id, dataset_id) 
                        VALUES (%s, %s, %s, %s)
                        """
                        for label_id in label_ids:
                            cursor.execute(insert_label_query, 
                                         (newfile_id, label_id, group_id, new_dataset_id))
                        conn.commit()
                        print(f"为文件 {filename} 添加了 {len(label_ids)} 个标签")
                    
                except Exception as e:
                    print(f"处理文件 {source_file} 时出错: {str(e)}")
                    conn.rollback()
            else:
                print(f"警告: 路径不是文件或不存在 - {source_file}")

        return new_dataset_id

    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
 
def merge_dataset(request_data, result):
    # 1. 解析前端请求数据
    name = request_data['new_dataset_name']
    group_id = request_data['group_id']
    dataset_ids = request_data.get('dataset_id', [])
    labels = request_data.get('labels', [])
    desc = request_data['desc']

    # 2. 创建目录
    base_path = r'C:\Users\admin\Desktop\flask\uploads'
    new_dir_path = os.path.join(base_path, name)
    os.makedirs(new_dir_path, exist_ok=True)
    
    try:
        # 3. 连接数据库
        conn = mysql.connector.connect(
            host="192.168.3.37",
            port = 3306,
            user="root",
            password="123456",
            database="dubhe-prod"
        )
        cursor = conn.cursor()

        # 4. 获取任意dataset_id对应的data_type
        if result and dataset_ids:
            dataset_id_to_query = result[0]['dataset_id']
        elif dataset_ids:
            dataset_id_to_query = dataset_ids[0]
        else:
            dataset_id_to_query = None

        if dataset_id_to_query:
            cursor.execute(
                "SELECT data_type FROM data_dataset_n WHERE id = %s",
                (dataset_id_to_query,)
            )
            data_type_row = cursor.fetchone()
            data_type = data_type_row[0] if data_type_row else 'default_type'
        else:
            data_type = 'default_type'

        # 5. 计算数据大小
        data_size = len(result)

        # 6. 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 7. 插入新数据集记录
        insert_dataset_query = """
        INSERT INTO data_dataset_n (
            name, data_type, uri, create_user_id, 
            create_time, update_time, status, 
            data_size, data_src_size, group_id,remark
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        dataset_values = (
            name,
            data_type,
            new_dir_path.replace('\\', '/'),
            'admin',
            current_time,
            current_time,
            2,
            data_size,
            data_size,
            group_id,
            desc
        )

        cursor.execute(insert_dataset_query, dataset_values)
        conn.commit()

        # 8. 获取新数据集的ID
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_dataset_id = cursor.fetchone()[0]
        
        # 9. 遍历并处理每个文件
        for item in result:
            source_file = item['file_url']
            # 处理路径格式
            source_file = source_file.replace('\\\\', '\\')
            
            # 只处理文件
            if os.path.isfile(source_file):
                # 获取文件名和后缀
                filename = os.path.basename(source_file)
                file_base, file_ext = os.path.splitext(filename)
                file_type = file_ext[1:] if file_ext else ''  # 去掉点号
                
                # 目标路径
                dest_path = os.path.join(new_dir_path, filename)
                
                try:
                    # 复制文件到根目录
                    shutil.copy2(source_file, dest_path)
                    print(f"成功复制到根目录: {source_file} -> {dest_path}")
                  
                    # 获取当前时间
                    file_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 插入文件记录
                    insert_file_query = """
                    INSERT INTO data_file_n (
                        name, status, dataset_id, file_url, 
                        create_user_id, create_time, file_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    file_values = (
                        file_base,  # 不带后缀的文件名
                        1,          # status=1
                        new_dataset_id,
                        dest_path.replace('\\', '/'),
                        'admin',
                        file_time,
                        file_type
                    )
                    
                    cursor.execute(insert_file_query, file_values)
                    conn.commit()
                    
                    # 获取新文件ID
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    newfile_id = cursor.fetchone()[0]
                    
                    # 获取原始文件ID和数据集ID
                    original_file_id = item['id']
                    original_dataset_id = item['dataset_id']
                    
                    # 查询标签关系
                    query_label_query = """
                    SELECT label_id 
                    FROM file_label_rela 
                    WHERE file_id = %s AND dataset_id = %s AND group_id = %s
                    """
                    cursor.execute(query_label_query, 
                                  (original_file_id, original_dataset_id, group_id))
                    label_ids = [row[0] for row in cursor.fetchall()]
                    
                    # 插入新标签关系
                    if label_ids:
                        insert_label_query = """
                        INSERT INTO file_label_rela 
                            (file_id, label_id, group_id, dataset_id) 
                        VALUES (%s, %s, %s, %s)
                        """
                        for label_id in label_ids:
                            cursor.execute(insert_label_query, 
                                         (newfile_id, label_id, group_id, new_dataset_id))
                        conn.commit()
                        print(f"为文件 {filename} 添加了 {len(label_ids)} 个标签")
                    
                except Exception as e:
                    print(f"处理文件 {source_file} 时出错: {str(e)}")
                    conn.rollback()
            else:
                print(f"警告: 路径不是文件或不存在 - {source_file}")

        return new_dataset_id

    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
    

def parse_query_params_datasetfile(params):
    """
    解析 ImmutableMultiDict 为统一结构的字典
    返回格式:
    {
        "labels": list | None,        # 新增字段
        "dataset_id": list | None,    # 现在可以是列表
        "file_type": list | None,
        "name": str | None,
        "pageNum": int,
        "pageSize": int
    }
    """
  # 初始化默认结构 - pageNum/pageSize 默认为 None
    query_params = {
        "labels": None,
        "dataset_id": None,
        "file_type": None,
        "name": None,
        "pageNum": None,  # 默认值改为 None
        "pageSize": None   # 默认值改为 None
    }
      # 处理分页参数 - 仅当参数存在且可转换时赋值
    if "pageNum" in params:
        try:
            query_params["pageNum"] = int(params["pageNum"])
        except (ValueError, TypeError):
            pass  # 保持 None

    if "pageSize" in params:
        try:
            query_params["pageSize"] = int(params["pageSize"])
        except (ValueError, TypeError):
            pass  # 保持 None
        


    # 通用 JSON 解析函数
    def parse_json_value(value):
        """尝试解析 JSON 值，失败返回原值"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    # 处理 dataset_id（支持单个值或多个值）
    if "dataset_id" in params:
        dataset_id = parse_json_value(params["dataset_id"])
        
        # 如果值是列表类型
        if isinstance(dataset_id, list):
            try:
                # 尝试转换为整数列表
                dataset_ids = [int(id) for id in dataset_id if id != ""]
                query_params["dataset_id"] = dataset_ids if dataset_ids else None
            except (ValueError, TypeError):
                query_params["dataset_id"] = None
        
        # 如果是字符串类型（逗号分隔）
        elif isinstance(dataset_id, str):
            try:
                # 分割字符串并转换为整数列表
                dataset_ids = [int(id.strip()) for id in dataset_id.split(",") if id.strip()]
                query_params["dataset_id"] = dataset_ids if dataset_ids else None
            except (ValueError, TypeError):
                query_params["dataset_id"] = None
        
        # 其他类型（单个值）
        else:
            try:
                # 尝试转换为整数
                dataset_id_val = int(dataset_id)
                query_params["dataset_id"] = [dataset_id_val]
            except (ValueError, TypeError):
                query_params["dataset_id"] = None
    
    # 处理 labels（可选字段）
    if "labels" in params:
        labels = parse_json_value(params["labels"])
        
        # 如果值是列表类型
        if isinstance(labels, list):
            try:
                # 尝试转换为整数列表
                query_params["labels"] = labels if labels else None
            except (ValueError, TypeError):
                query_params["labels"] = None
        
        # 如果是字符串类型（逗号分隔）
        elif isinstance(labels, str):
            try:
                # 分割字符串并转换为整数列表
                label_ids = [int(id.strip()) for id in labels.split(",") if id.strip()]
                query_params["labels"] = label_ids if label_ids else None
            except (ValueError, TypeError):
                query_params["labels"] = None
        
        # 其他类型（单个值）
        else:
            try:
                # 尝试转换为整数
                label_id_val = int(labels)
                query_params["labels"] = [label_id_val]
            except (ValueError, TypeError):
                query_params["labels"] = None
    else:
        # 如果未提供 labels 参数
        query_params["labels"] = None

    # 处理 file_type（多选类型）
    if "file_type" in params:
        file_types = parse_json_value(params["file_type"])
        
        # 如果值是列表类型
        if isinstance(file_types, list):
            # 过滤空值
            file_types = [ft for ft in file_types if ft != ""]
            query_params["file_type"] = file_types if file_types else None
        
        # 如果是字符串类型（逗号分隔）
        elif isinstance(file_types, str):
            # 分割字符串并过滤空值
            file_types = [ft.strip() for ft in file_types.split(",") if ft.strip()]
            query_params["file_type"] = file_types if file_types else None
        
        # 其他类型
        else:
            query_params["file_type"] = None

    # 处理名称条件
    if "name" in params:
        name = params["name"].strip()  # 去除前后空格
        query_params["name"] = name if name else None  # 空字符串转为None

    return query_params  # 确保返回解析结果
import json

def parse_query_params_make_dataset(params):
    """
    解析请求参数为统一结构的字典
    返回格式:
    {
        "name": str | None,
        "desc": str | None,
        "dataset_id": list | None,
        "labels": list | None,
        "group_id": int | None,
        "pageNum": int | None,
        "pageSize": int | None
    }
    """
    # 初始化默认结构
    query_params = {
        "name": None,
        "desc": None,
        "dataset_id": None,
        "labels": None,
        "group_id": None,
        "pageNum": None,
        "pageSize": None
    }

    # 处理分页参数
    if "pageNum" in params:
        try:
            query_params["pageNum"] = int(params["pageNum"])
        except (ValueError, TypeError):
            pass

    if "pageSize" in params:
        try:
            query_params["pageSize"] = int(params["pageSize"])
        except (ValueError, TypeError):
            pass

    # 通用 JSON 解析函数
    def parse_json_value(value):
        """尝试解析 JSON 值，失败返回原值"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    # 处理 name
    if "name" in params:
        name = params["name"]
        if isinstance(name, str):
            name = name.strip()
            if name:
                query_params["name"] = name
        elif name is not None:  # 处理非字符串类型
            query_params["name"] = str(name)

    # 处理 desc
    if "desc" in params:
        desc = params["desc"]
        if isinstance(desc, str):
            desc = desc.strip()
            if desc:
                query_params["desc"] = desc
        elif desc is not None:
            query_params["desc"] = str(desc)

    # 处理 group_id
    if "group_id" in params:
        try:
            group_id = params["group_id"]
            # 如果是字符串，尝试转换为整数
            if isinstance(group_id, str):
                group_id = group_id.strip()
                if group_id:
                    query_params["group_id"] = int(group_id)
            else:
                query_params["group_id"] = int(group_id)
        except (ValueError, TypeError):
            pass

    # 处理 dataset_id
    if "dataset_id" in params:
        dataset_id = parse_json_value(params["dataset_id"])
        
        # 如果值是列表类型
        if isinstance(dataset_id, list):
            try:
                # 尝试转换为整数列表
                dataset_ids = [int(id) for id in dataset_id if id != ""]
                query_params["dataset_id"] = dataset_ids if dataset_ids else None
            except (ValueError, TypeError):
                query_params["dataset_id"] = None
        
        # 如果是字符串类型（逗号分隔）
        elif isinstance(dataset_id, str):
            try:
                # 分割字符串并转换为整数列表
                dataset_ids = [int(id.strip()) for id in dataset_id.split(",") if id.strip()]
                query_params["dataset_id"] = dataset_ids if dataset_ids else None
            except (ValueError, TypeError):
                query_params["dataset_id"] = None
        
        # 其他类型（单个值）
        else:
            try:
                # 尝试转换为整数
                dataset_id_val = int(dataset_id)
                query_params["dataset_id"] = [dataset_id_val]
            except (ValueError, TypeError):
                query_params["dataset_id"] = None

    # 处理 labels（可选字段）
    if "labels" in params:
        labels = parse_json_value(params["labels"])
        
        # 如果值是列表类型
        if isinstance(labels, list):
            try:
                # 尝试转换为整数列表
                query_params["labels"] = labels if labels else None
            except (ValueError, TypeError):
                query_params["labels"] = None
        
        # 如果是字符串类型（逗号分隔）
        elif isinstance(labels, str):
            try:
                # 分割字符串并转换为整数列表
                label_ids = [int(id.strip()) for id in labels.split(",") if id.strip()]
                query_params["labels"] = label_ids if label_ids else None
            except (ValueError, TypeError):
                query_params["labels"] = None
        
        # 其他类型（单个值）
        else:
            try:
                # 尝试转换为整数
                label_id_val = int(labels)
                query_params["labels"] = [label_id_val]
            except (ValueError, TypeError):
                query_params["labels"] = None
    else:
        # 如果未提供 labels 参数
        query_params["labels"] = None

    return query_params

def insert_data_file_n(name, status,dataset_id,file_url,create_user_id,create_time,file_type):
    """
    使用连接池插入数据
    """
    connection = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        
        insert_query = "INSERT INTO data_file_n (name, status,dataset_id,file_url,create_user_id,create_time,file_type) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(insert_query, (name,status,dataset_id,file_url,create_user_id,create_time,file_type))
        connection.commit()
        
        return cursor.lastrowid
        
    except Error as e:
        print(f"插入用户 {name} 时出错: {e}")
        if connection:
            connection.rollback()
        return None
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()  # 返回到连接池
# def select_datasetfile_list_by_condition(query_params):
#     """
#     根据前端传递的参数动态查询文件列表，并添加标签名称拼接（按级别排序）
#     更新后的参数格式示例:
#     {
#         "dataset_id": 1,          # 必选参数
#         "file_type": ["png", "jpg"], # 多选类型（OR关系）
#         "name": "hello.jpg",       # 模糊匹配
#         "pageNum": 1,              # 页码
#         "pageSize": 10             # 每页数量
#     }
#     """
#     connection = None
#     cursor = None
#     try:
#         # 从连接池获取连接
#         connection = connection_pool.get_connection()
#         cursor = connection.cursor(dictionary=True)
        
#         # 基础查询语句
#         base_query = "FROM data_file_n WHERE dataset_id = %s"
        
#         # 参数集合（使用列表存储参数值）
#         params = [query_params['dataset_id']]
        
#         # 动态构建WHERE条件
#         conditions = []
        
#         # 1. 处理文件类型条件（多选OR关系）
#         file_types = query_params.get('file_type')
#         if file_types and isinstance(file_types, list) and file_types:
#             # 创建IN语句占位符
#             placeholders = ', '.join(['%s'] * len(file_types))
#             conditions.append(f"file_type IN ({placeholders})")
#             # 添加文件类型参数值
#             params.extend(file_types)
        
#         # 2. 处理名称模糊匹配
#         name = query_params.get('name')
#         if name:
#             conditions.append("name LIKE %s")
#             params.append(f"%{name}%")
        
#         # 组合完整的WHERE子句
#         if conditions:
#             base_query += " AND " + " AND ".join(conditions)
        
#         # 计算分页偏移量
#         offset = (query_params['pageNum'] - 1) * query_params['pageSize']
#         page_size = query_params['pageSize']
        
#         # 构建最终查询语句（分页）
#         data_query = f"""
#         SELECT * 
#         {base_query}
#         ORDER BY id
#         LIMIT %s, %s;
#         """
        
#         # 添加分页参数
#         params.extend([offset, page_size])
        
#         # 执行数据查询（使用位置参数）
#         cursor.execute(data_query, params)
#         results = cursor.fetchall()
        
#         # 构建总数查询（不需要分页参数）
#         count_query = f"SELECT COUNT(*) AS total {base_query};"
        
#         # 执行总数查询（移除最后两个分页参数）
#         cursor.execute(count_query, params[:-2])
#         total_records = cursor.fetchone()['total']
        
#         # ============ 新增部分：添加标签名称拼接（按级别排序） ============
        
#         # 1. 获取数据集对应的组ID
#         group_query = """
#         SELECT group_id 
#         FROM data_dataset_n 
#         WHERE id = %s
#         """
#         cursor.execute(group_query, (query_params['dataset_id'],))
#         group_result = cursor.fetchone()
        
#         if not group_result:
#             # 如果没有找到组ID，为所有文件添加空标签
#             for file in results:
#                 file['label_name'] = ""
#             return {
#                 "records": results,
#                 "total": total_records,
#                 "pageNum": query_params['pageNum'],
#                 "pageSize": query_params['pageSize']
#             }
        
#         group_id = group_result['group_id']
        
#         # 2. 获取当前页所有文件的ID
#         file_ids = [str(file['id']) for file in results]
        
#         if not file_ids:
#             # 如果没有文件，直接返回
#             return {
#                 "records": results,
#                 "total": total_records,
#                 "pageNum": query_params['pageNum'],
#                 "pageSize": query_params['pageSize']
#             }
        
#         # 3. 查询这些文件在指定组下的标签关联
#         placeholders = ', '.join(['%s'] * len(file_ids))
#         label_rela_query = f"""
#         SELECT fl.file_id, fl.label_id
#         FROM file_label_rela fl
#         WHERE fl.dataset_id = %s
#           AND fl.group_id = %s
#           AND fl.file_id IN ({placeholders})
#         """
#         label_params = [query_params['dataset_id'], group_id] + file_ids
#         cursor.execute(label_rela_query, label_params)
#         label_rels = cursor.fetchall()
        
#         # 4. 按文件ID分组标签ID
#         file_labels = {}
#         for rel in label_rels:
#             file_id = rel['file_id']
#             label_id = rel['label_id']
#             if file_id not in file_labels:
#                 file_labels[file_id] = []
#             file_labels[file_id].append(str(label_id))
        
#         # 5. 获取所有标签的名称和级别
#         all_label_ids = set()
#         for labels in file_labels.values():
#             all_label_ids.update(labels)
        
#         label_info = {}  # 存储标签的完整信息
#         if all_label_ids:
#             label_placeholders = ', '.join(['%s'] * len(all_label_ids))
#             label_name_query = f"""
#             SELECT label_id, label_name, level
#             FROM label_info
#             WHERE label_id IN ({label_placeholders})
#             """
#             cursor.execute(label_name_query, list(all_label_ids))
#             for row in cursor.fetchall():
#                 label_id_str = str(row['label_id'])
#                 label_info[label_id_str] = {
#                     'name': row['label_name'],
#                     'level': row['level']  # 添加级别信息
#                 }
        
#         # 6. 为每个文件构建标签名称字符串（按级别排序）
#         for file in results:
#             file_id = file['id']
#             file_id_str = str(file_id)
            
#             if file_id_str in file_labels:
#                 # 获取该文件的所有标签信息
#                 labels = []
#                 for label_id in file_labels[file_id_str]:
#                     if label_id in label_info:
#                         labels.append(label_info[label_id])
                
#                 # 按级别从小到大排序
#                 labels_sorted = sorted(labels, key=lambda x: x['level'])
                
#                 # 提取排序后的标签名称
#                 names = [label['name'] for label in labels_sorted]
                
#                 # 过滤空值并连接
#                 file['label_name'] = '-'.join(filter(None, names))
#             else:
#                 file['label_name'] = ""
        
#         # ============ 新增部分结束 ============
        
#         return {
#             "records": results,
#             "total": total_records,
#             "pageNum": query_params['pageNum'],
#             "pageSize": query_params['pageSize']
#         }
        
#     except Exception as e:
#         print(f"文件查询出错: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return {
#             "records": [],
#             "total": 0,
#             "pageNum": query_params.get('pageNum', 1),
#             "pageSize": query_params.get('pageSize', 10)
#         }
        
#     finally:
#         # 关闭资源
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()

def select_datasetfile_list_by_condition(query_params):
    """
    根据前端传递的参数动态查询文件列表，并添加标签名称拼接和统计
    更新后的参数格式示例:
    {
        "labels": [['10'], [], ['11'], [], []],  # 新的标签结构
        "dataset_id": [1, 507],    # 必选参数（列表）
        "file_type": ["png", "jpg"], # 多选类型（OR关系）
        "name": "hello.jpg",       # 模糊匹配
        "pageNum": 1,              # 页码（可为None表示不分页）
        "pageSize": 10             # 每页数量（可为None表示不分页）
    }
    """
    connection = None
    cursor = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 基础查询语句
        dataset_ids = query_params['dataset_id']
        if not isinstance(dataset_ids, list):
            dataset_ids = [dataset_ids]
        
        # 构建 dataset_id 的 IN 条件
        dataset_placeholders = ', '.join(['%s'] * len(dataset_ids))
        base_query = f"FROM data_file_n WHERE dataset_id IN ({dataset_placeholders})"
        
        # 参数集合（使用列表存储参数值）
        params = dataset_ids.copy()  # 复制数据集ID列表
        
        # 动态构建WHERE条件
        conditions = []
        
        # 1. 处理文件类型条件（多选OR关系）
        file_types = query_params.get('file_type')
        if file_types and isinstance(file_types, list) and file_types:
            # 创建IN语句占位符
            placeholders = ', '.join(['%s'] * len(file_types))
            conditions.append(f"file_type IN ({placeholders})")
            # 添加文件类型参数值
            params.extend(file_types)
        
        # 2. 处理名称模糊匹配
        name = query_params.get('name')
        if name:
            conditions.append("name LIKE %s")
            params.append(f"%{name}%")
        
        # 组合完整的WHERE子句
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # ============ 处理分页参数 ============
        page_num = query_params.get('pageNum')
        page_size = query_params.get('pageSize')
        
        # 构建数据查询语句（分页或无分页）
        if page_num is not None and page_size is not None:
            # 计算分页偏移量
            offset = (page_num - 1) * page_size
            # 构建分页查询
            data_query = f"""
            SELECT * 
            {base_query}
            ORDER BY id
            LIMIT %s, %s;
            """
            # 添加分页参数
            params.extend([offset, page_size])
        else:
            # 无分页查询
            data_query = f"""
            SELECT * 
            {base_query}
            ORDER BY id;
            """
        
        # 执行数据查询（使用位置参数）
        cursor.execute(data_query, params)
        results = cursor.fetchall()
        
        # 构建总数查询（不需要分页参数）
        count_query = f"SELECT COUNT(*) AS total {base_query};"
        
        # 执行总数查询（使用相同的参数，但不包括分页参数）
        count_params = params
        if page_num is not None and page_size is not None:
            # 移除最后两个分页参数
            count_params = params[:-2]
        
        cursor.execute(count_query, count_params)
        total_records = cursor.fetchone()['total']
        
        # ============ 标签过滤逻辑 - 按数据集独立筛选 ============
        labels = query_params.get('labels', [])
        if labels:
            # 确保labels有5个元素（对应5个级别）
            if len(labels) < 5:
                labels.extend([[]] * (5 - len(labels)))
            
            # 按数据集分组文件
            dataset_files = {}
            for file in results:
                dataset_id = file['dataset_id']
                if dataset_id not in dataset_files:
                    dataset_files[dataset_id] = []
                dataset_files[dataset_id].append(file)
            
            # 为每个数据集筛选符合条件的文件
            valid_files = []
            for dataset_id, files in dataset_files.items():
                # 收集当前数据集的文件ID
                file_ids = [str(file['id']) for file in files]
                
                # 存储每个级别的有效文件ID集合
                level_sets = []
                
                # 处理每个级别（1-5）
                for level_index, level_labels in enumerate(labels):
                    level = level_index + 1  # 级别从1开始
                    
                    # 如果该级别有选择的标签
                    if level_labels and isinstance(level_labels, list):
                        # 转换标签ID为字符串
                        label_ids = [str(label_id) for label_id in level_labels]
                        
                        # 构建查询
                        label_placeholders = ', '.join(['%s'] * len(label_ids))
                        level_query = f"""
                        SELECT DISTINCT file_id
                        FROM file_label_rela
                        WHERE file_id IN ({', '.join(['%s'] * len(file_ids))})
                          AND label_id IN ({label_placeholders})
                          AND dataset_id = %s  # 添加数据集条件
                        """
                        
                        # 参数：文件ID + 标签ID + 数据集ID
                        level_params = file_ids + label_ids + [dataset_id]
                        cursor.execute(level_query, level_params)
                        level_file_ids = {str(row['file_id']) for row in cursor.fetchall()}
                        level_sets.append(level_file_ids)
                    
                    # 如果该级别没有选择标签，则跳过过滤
                    else:
                        level_sets.append(set(file_ids))  # 包含所有文件
                
                # 取所有级别的交集（AND关系）
                if level_sets:
                    valid_file_ids = set.intersection(*level_sets)
                    # 添加符合条件的文件
                    valid_files.extend([file for file in files if str(file['id']) in valid_file_ids])
            
            # 更新结果集
            results = valid_files
        
        # ============ 标签名称拼接部分（修改为五级列表结构） ============
        if results:
            # 收集所有文件ID
            file_ids = [str(file['id']) for file in results]
            
            # 查询这些文件的标签关联
            placeholders = ', '.join(['%s'] * len(file_ids))
            label_rela_query = f"""
            SELECT fl.file_id, fl.label_id, fl.dataset_id
            FROM file_label_rela fl
            WHERE fl.file_id IN ({placeholders})
            """
            
            cursor.execute(label_rela_query, file_ids)
            label_rels = cursor.fetchall()
            
            # 按文件ID分组标签ID
            file_labels = {}
            for rel in label_rels:
                file_id = str(rel['file_id'])
                if file_id not in file_labels:
                    file_labels[file_id] = []
                file_labels[file_id].append(str(rel['label_id']))
            
            # 获取所有标签的名称和级别
            all_label_ids = set()
            for labels in file_labels.values():
                all_label_ids.update(labels)
            
            label_info = {}  # 存储标签的完整信息
            if all_label_ids:
                label_placeholders = ', '.join(['%s'] * len(all_label_ids))
                label_name_query = f"""
                SELECT label_id, label_name, level
                FROM label_info
                WHERE label_id IN ({label_placeholders})
                """
                cursor.execute(label_name_query, list(all_label_ids))
                for row in cursor.fetchall():
                    label_id_str = str(row['label_id'])
                    label_info[label_id_str] = {
                        'name': row['label_name'],
                        'level': row['level']
                    }
            
            # 为每个文件构建五级标签名称列表
            for file in results:
                file_id = str(file['id'])
                
                # 初始化五级空列表
                label_names_by_level = [[] for _ in range(5)]
                
                if file_id in file_labels:
                    # 收集该文件的所有标签信息
                    for label_id in file_labels[file_id]:
                        if label_id in label_info:
                            label = label_info[label_id]
                            level = label['level']
                            
                            # 确保级别在1-5范围内
                            if 1 <= level <= 5:
                                # 级别对应索引
                                idx = level - 1
                                label_names_by_level[idx].append(label['name'])
                
                # 将标签名称列表添加到文件结果中
                file['label_names'] = label_names_by_level
        else:
            # 如果没有结果，确保每个文件都有 label_names 字段
            for file in results:
                file['label_names'] = [[] for _ in range(5)]
        
        # ============ 统计标签组合数量（使用五级列表结构） ============
        label_statistics = {}
        total_count = len(results)  # 实际返回的记录数（可能经过标签过滤）
        
        for file in results:
            # 创建可哈希的键 - 将每级标签名称列表转换为元组
            key = tuple(tuple(level) for level in file['label_names'])
            
            if key not in label_statistics:
                label_statistics[key] = 0
            label_statistics[key] += 1
        
        # 将统计结果转换为前端友好的格式
        label_statistics_list = []
        for key, count in label_statistics.items():
            # 将元组转换回嵌套列表
            label_names_list = [list(level) for level in key]
            label_statistics_list.append({
                "label_names": label_names_list,
                "count": count
            })
        
        return {
            "records": results,
            "total": total_records,  # 基础查询的总记录数
            "total_counts": total_count,  # 实际返回的记录数（可能经过标签过滤）
            "pageNum": page_num,      # 可能为None
            "pageSize": page_size,    # 可能为None
            "label_statistics": label_statistics_list
        }
        
    except Exception as e:
        print(f"文件查询出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "records": [],
            "total": 0,
            "pageNum": query_params.get('pageNum'),
            "pageSize": query_params.get('pageSize'),
            "label_statistics": []
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    # 示例查询参数
    # query_params = {
    #     "labels": ["3","4"],       # 需要匹配的标签ID
    #     "dataset_id": ["507","508"],    # 数据集ID列表
    #     "file_type": None,      # 文件类型
    #     "name": None,             # 文件名模糊匹配
    #     "pageNum": 1,              # 页码
    #     "pageSize": 10             # 每页数量
    # }

    # # 执行查询
    # result = select_datasetfile_list_by_condition(query_params)
    # print(f"总记录数: {result['total']}")
    # print(f"当前页数据: {result['records']}")
    # result = select_data_standard_attr(1)
    # print(result)  # 输出: ['CoHH', 'CoHV', 'CoVH']
    #result = select_dataset_list_by_condition(query_params)
    #print(delete_dataset_by_id(8))
    # 返回结果示例
    #print(f"总记录数: {result['total']}")
    #print(f"当前页数据: {result['records']}")
    clear_files_in_folder("uploads/sbsbsbs")