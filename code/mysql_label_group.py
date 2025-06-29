import datetime
import json
from mysql.connector import pooling
from pymysql import Error


connection_pool = pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    host='192.168.3.37',
    port=3306,
    user='root',
    password='123456',
    database='dubhe-prod'
)


def insert_file_label_rela_and_update_status(data_list):
    """
    插入文件标签关联记录并更新文件状态（先删除旧记录）
    参数格式示例:
    [
        {
            "dataset_id": 507,
            "file_id": 3,
            "group_id": "2",
            "label_id": "8"
        },
        {
            "dataset_id": 507,
            "file_id": 3,
            "group_id": "2",
            "label_id": "6"
        }
    ]
    """
    connection = None
    cursor = None
    data_list = json.loads(data_list)
    try:
        # 检查输入是否为空且为列表类型
        if not data_list:
            return {
                "success": False,
                "message": "传入的数据列表为空"
            }
        
        # 确保传入的是列表而不是单个整数
        if not isinstance(data_list, list):
            # 如果传入的是单个字典对象，将其转换为列表
            if isinstance(data_list, dict):
                data_list = [data_list]
            else:
                return {
                    "success": False,
                    "message": "传入的数据必须是列表或字典"
                }
        
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        
        # 准备批量插入的参数
        params_list = []
        file_ids = set()  # 用于收集所有唯一的 file_id
        
        for data in data_list:
            # 确保每个元素是字典
            if not isinstance(data, dict):
                return {
                    "success": False,
                    "message": "列表中的每个元素必须是字典类型"
                }
            
            # 验证每个对象是否包含必要字段
            required_fields = ['file_id', 'label_id', 'group_id', 'dataset_id']
            if not all(field in data for field in required_fields):
                return {
                    "success": False,
                    "message": f"缺少必要字段，需要包含: {', '.join(required_fields)}"
                }
            
            # 收集 file_id
            file_ids.add(data['file_id'])
            
            # 准备插入参数
            params_list.append({
                'file_id': str(data['file_id']),
                'label_id': str(data['label_id']),
                'group_id': str(data['group_id']),
                'dataset_id': str(data['dataset_id'])
            })
        
        # 1. 删除相同 file_id 的所有旧记录
        if file_ids:
            # 创建占位符字符串 (%s, %s, %s)
            placeholders = ', '.join(['%s'] * len(file_ids))
            
            # 构建删除语句
            delete_query = f"""
            DELETE FROM file_label_rela 
            WHERE file_id IN ({placeholders})
            """
            
            # 执行删除操作
            cursor.execute(delete_query, tuple(file_ids))
            deleted_count = cursor.rowcount
            print(f"已删除 {deleted_count} 条旧记录")
        
        # 2. 插入新的文件标签关联记录
        # 构建插入语句
        insert_query = """
        INSERT INTO file_label_rela 
            (file_id, label_id, group_id, dataset_id)
        VALUES 
            (%(file_id)s, %(label_id)s, %(group_id)s, %(dataset_id)s)
        """
        
        # 执行批量插入操作
        cursor.executemany(insert_query, params_list)
        inserted_count = cursor.rowcount
        
        # 3. 更新文件状态
        if file_ids:
            # 构建更新语句
            update_query = f"""
            UPDATE data_file_n 
            SET status = 1 
            WHERE id IN ({placeholders})  # 使用相同的占位符
            """
            
            # 执行更新操作
            cursor.execute(update_query, tuple(file_ids))
            updated_count = cursor.rowcount
        
        # 提交事务
        connection.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count if 'deleted_count' in locals() else 0,
            "inserted_count": inserted_count,
            "updated_count": updated_count if 'updated_count' in locals() else 0,
            "message": f"已删除 {deleted_count} 条旧记录，插入 {inserted_count} 条新记录，更新 {updated_count} 个文件状态"
        }
        
    except Error as e:
        # 发生错误时回滚事务
        if connection:
            connection.rollback()
        print(f"操作失败: {e}")
        return {
            "success": False,
            "message": f"操作失败: {str(e)}"
        }
        
    except Exception as e:
        # 捕获其他异常
        if connection:
            connection.rollback()
        print(f"处理过程中发生错误: {e}")
        return {
            "success": False,
            "message": f"处理过程中发生错误: {str(e)}"
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def insert_label_info(label_info):
    """
    将前端传递的标签信息插入到标签表中
    参数格式示例:
    {
        "desc": "标签描述文本",
        "group_id": "1",       # 所属标签组ID
        "userId": "admin",     # 创建用户ID
        "level": "1",          # 标签级别
        "label_name": "标签名称"
    }
    """
    connection = None
    cursor = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        
        # 如果传入的是JSON字符串，则解析为字典
       
        label_info = json.loads(label_info)
        
        # 构建插入语句
        insert_query = """
        INSERT INTO label_info 
            (label_name, level, create_user_id, create_time, `desc`)
        VALUES 
            (%(label_name)s, %(level)s, %(userId)s, NOW(), %(desc)s)
        """
        
        # 准备参数
        params = {
            'label_name': label_info['label_name'],
            'level': label_info['level'],
            'userId': label_info['userId'],
            'desc': label_info.get('desc', '')
        }
        
        # 执行插入操作
        cursor.execute(insert_query, params)
        connection.commit()  # 提交事务
        group_id = label_info['group_id']
        # 获取新插入的ID
        new_id = cursor.lastrowid
        query = """
        INSERT INTO label_group_rela 
            (group_id,label_id)
        VALUES 
            (%s, %s)
            """
        cursor.execute(query,(group_id,new_id))
        connection.commit() 
        return {
            "success": True,
            "labelId": new_id,
            "message": "标签创建成功"
        }
        
    except Error as e:
        # 发生错误时回滚事务
        if connection:
            connection.rollback()
        print(f"标签创建失败: {e}")
        return {
            "success": False,
            "labelId": None,
            "message": f"标签创建失败: {str(e)}"
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return {
            "success": False,
            "labelId": None,
            "message": "参数格式不正确，必须是有效的JSON"
        }
        
    except KeyError as e:
        print(f"缺少必要参数: {e}")
        return {
            "success": False,
            "labelId": None,
            "message": f"缺少必要参数: {str(e)}"
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def insert_label_group_info(group_info):
    """
    将前端传递的标签组信息插入到label_group_info表中
    参数格式示例:
    {
        "desc": "组描述文本",
        "group_name": "标签组名称",
        "userId": "admin"
    }
    """
    connection = None
    cursor = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        
        # 构建插入语句
        insert_query = """
        INSERT INTO label_group_info 
            (group_name, create_user_id, create_time, `desc`)
        VALUES 
            (%(group_name)s, %(userId)s, NOW(), %(desc)s)
        """
        group_info = json.loads(group_info)
        # 准备参数（注意：desc是MySQL关键字，需要特殊处理）
        params = {
            'group_name': group_info['group_name'],
            'userId': group_info['userId'],
            'desc': group_info.get('desc', '')  # 使用get避免KeyError
        }
        
        # 执行插入操作
        cursor.execute(insert_query, params)
        connection.commit()  # 提交事务
        
        # 获取新插入的ID
        new_id = cursor.lastrowid
        
        return {
            "success": True,
            "groupId": new_id,
            "message": "标签组创建成功"
        }
        
    except Error as e:
        # 发生错误时回滚事务
        if connection:
            connection.rollback()
        print(f"标签组创建失败: {e}")
        return {
            "success": False,
            "groupId": None,
            "message": f"标签组创建失败: {str(e)}"
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def select_label_group_list_by_condition(query_params):
    """
    根据前端传递的参数动态查询标签组列表
    参数格式示例:
    {
        "desc": "123",        # 描述模糊匹配（可选）
        "group_name": "test",  # 组名模糊匹配（可选）
        "userId": "1",         # 用户ID（必选）
        "pageNum": 1,          # 页码（可选）
        "pageSize": 20         # 每页数量（可选）
    }
    """
    connection = None
    cursor = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 基础查询语句
        base_query = """
        FROM label_group_info
        WHERE create_user_id = %(userId)s
        """
        
        # 参数集合初始化
        params = {
            'userId': query_params['userId']
        }
        
        # 动态构建WHERE条件
        conditions = []
        
        # 添加group_name条件（模糊匹配）
        if query_params.get('group_name'):
            conditions.append("group_name LIKE %(group_name)s")
            params['group_name'] = f"%{query_params['group_name']}%"
        
        # 添加desc条件（模糊匹配，注意desc是MySQL关键字）
        if query_params.get('desc'):
            conditions.append("`desc` LIKE %(desc)s")
            params['desc'] = f"%{query_params['desc']}%"
        
        # 组合完整的WHERE子句
        where_clause = base_query
        if conditions:
            where_clause += " AND " + " AND ".join(conditions)
        
        # 构建数据查询语句
        query = f"""
        SELECT *
        {where_clause}
        ORDER BY group_id 
        """
        
        # 判断是否需要分页
        has_pagination = ('pageNum' in query_params and 
                        'pageSize' in query_params and 
                        query_params['pageNum'] is not None and 
                        query_params['pageSize'] is not None)
        
        if has_pagination:
            # 添加分页参数
            params['offset'] = (query_params['pageNum'] - 1) * query_params['pageSize']
            params['pageSize'] = query_params['pageSize']
            query += "LIMIT %(offset)s, %(pageSize)s"
        
        # 添加结束分号
        query += ";"
        
        # 执行查询
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 获取总数（用于分页统计）
        count_query = f"SELECT COUNT(*) AS total {where_clause};"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()['total']
        
        # 构建返回结果
        response = {
            "records": results,
            "total": total_records
        }
        
        # 只有在有分页参数时才返回分页信息
        if has_pagination:
            response.update({
                "pageNum": query_params['pageNum'],
                "pageSize": query_params['pageSize']
            })
        
        return response
        
    except Error as e:
        print(f"标签组查询出错: {e}")
        import traceback
        traceback.print_exc()
        return {
            "records": [],
            "total": 0
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()
def parse_query_params_label_group(params):
    """
    解析请求参数为统一结构的字典
    返回格式:
    {
        "desc": str | None,      # 描述模糊匹配（可选）
        "group_name": str | None, # 组名模糊匹配（可选）
        "userId": str | None,    # 用户ID（必选）
        "pageNum": int | None,    # 页码（可选）
        "pageSize": int | None    # 每页数量（可选）
    }
    """
    # 初始化默认结构
    query_params = {
        "desc": None,
        "group_name": None,
        "pageNum": None,    # 默认不分页
        "pageSize": None,   # 默认不分页
        "userId": None      # 必填字段初始为None
    }

    # 处理分页参数（带类型转换）
    if "pageNum" in params:
        try:
            page_num = int(params["pageNum"])
            if page_num > 0:  # 确保页码有效
                query_params["pageNum"] = page_num
        except (ValueError, TypeError):
            pass  # 保持None

    if "pageSize" in params:
        try:
            page_size = int(params["pageSize"])
            if page_size > 0 and page_size <= 1000:  # 限制1-1000
                query_params["pageSize"] = page_size
        except (ValueError, TypeError):
            pass  # 保持None

    # 处理必填字段（userId）
    if "userId" in params:
        user_id = params["userId"]
        query_params["userId"] = user_id if user_id else None  # 空字符串转为None

    # 处理可选字段（desc和group_name）
    if "desc" in params:
        desc = params["desc"]
        query_params["desc"] = desc if desc else None  # 空字符串转为None

    if "group_name" in params:
        group_name = params["group_name"]
        query_params["group_name"] = group_name if group_name else None

    return query_params
def parse_query_params_label_list(params):
    """
    解析标签列表查询参数为统一结构的字典
    返回格式:
    {
        "group_id": int | None,  # 标签组ID（必选）
        "pageNum": int | None,    # 页码（可选，None表示不分页）
        "pageSize": int | None    # 每页数量（可选，None表示不分页）
    }
    """
    # 初始化默认结构
    query_params = {
        "group_id": None,
        "pageNum": None,    # 默认不分页
        "pageSize": None    # 默认不分页
    }

    # 处理分页参数（带类型转换）
    if "pageNum" in params:
        try:
            page_num = int(params["pageNum"])
            if page_num > 0:  # 确保页码有效
                query_params["pageNum"] = page_num
        except (ValueError, TypeError):
            pass  # 保持None

    if "pageSize" in params:
        try:
            page_size = int(params["pageSize"])
            if page_size > 0 and page_size <= 1000:  # 限制1-1000
                query_params["pageSize"] = page_size
        except (ValueError, TypeError):
            pass  # 保持None

    # 处理必填字段（group_id）
    if "group_id" in params:
        try:
            # 将group_id转为整数
            query_params["group_id"] = int(params["group_id"])
        except (ValueError, TypeError):
            # 转换失败保持None
            pass

    return query_params

def select_label_list_by_group_id(query_params):
    """
    根据标签组ID查询对应的标签列表（可选分页）
    参数格式:
    {
        "group_id": "1",   # 标签组ID（必选）
        "pageNum": 1,       # 页码（可选）
        "pageSize": 20      # 每页数量（可选）
    }
    """
    connection = None
    cursor = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 验证必填参数
        group_id = query_params.get('group_id')
        if not group_id:
            raise ValueError("缺少必填参数: group_id")
        
        # 判断是否需要分页
        has_pagination = ('pageNum' in query_params and 
                         'pageSize' in query_params and 
                         query_params['pageNum'] is not None and 
                         query_params['pageSize'] is not None)
        
        # 构建主查询语句（使用JOIN查询）
        data_query = """
        SELECT li.* 
        FROM label_info li
        JOIN label_group_rela lgr ON li.label_id = lgr.label_id
        WHERE lgr.group_id = %s
        ORDER BY li.label_id
        """
        
        # 添加分页条件（如果需要）
        if has_pagination:
            offset = (query_params['pageNum'] - 1) * query_params['pageSize']
            page_size = query_params['pageSize']
            data_query += " LIMIT %s, %s"
            query_params = (group_id, offset, page_size)
        else:
            query_params = (group_id,)
        
        data_query += ";"
        
        # 执行数据查询
        cursor.execute(data_query, query_params)
        results = cursor.fetchall()
        
        # 构建总数查询语句
        count_query = """
        SELECT COUNT(*) AS total
        FROM label_info li
        JOIN label_group_rela lgr ON li.label_id = lgr.label_id
        WHERE lgr.group_id = %s;
        """
        
        # 执行总数查询
        cursor.execute(count_query, (group_id,))
        total_records = cursor.fetchone()['total']
        
        # 构建返回结果
        response = {
            "records": results,
            "total": total_records
        }
        
        # 只有在有分页时才返回分页信息
        if has_pagination:
            response.update({
                "pageNum": query_params[1] + 1 if has_pagination else None,
                "pageSize": query_params[2] if has_pagination else None
            })
        
        return response
        
    except Error as e:
        print(f"标签查询出错: {e}")
        import traceback
        traceback.print_exc()
        return {
            "records": [],
            "total": 0
        }
        
    except ValueError as e:
        print(f"参数验证失败: {e}")
        return {
            "records": [],
            "total": 0,
            "error": str(e)
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    # 调用示例
    result = select_label_group_list_by_condition({
        "desc": "",
        "group_name": "",
        "userId": "admin",
        "pageNum": 1,
        "pageSize": 10
    })

    print(f"找到 {result['total']} 条记录，当前页 {len(result['records'])} 条")
    for group in result['records']:
        print(f"ID: {group['group_id']}, 名称: {group['group_name']}")