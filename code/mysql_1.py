import datetime
from mysql.connector import pooling
from pymysql import Error

def parse_query_params(params):
    """
    解析 ImmutableMultiDict 为统一结构的字典
    返回格式:
    {
        "name": str | None,
        "data_type": int | None,
        "pageNum": int,
        "pageSize": int,
        "userId": str,
        "group_id": int | None  # 新增字段
    }
    """
    # 初始化默认结构
    query_params = {
        "name": None,
        "data_type": None,
        "pageNum": 1,  # 默认值
        "pageSize": 10,  # 默认值
        "userId": None,
        "group_id": None  # 新增字段
    }

    # 处理必填字段（带类型转换）
    try:
        query_params["pageNum"] = int(params.get("pageNum", 1))
    except (ValueError, TypeError):
        pass  # 保持默认值

    try:
        query_params["pageSize"] = int(params.get("pageSize", 10))
    except (ValueError, TypeError):
        pass

    # 处理必填字符串字段
    if "userId" in params:
        query_params["userId"] = params["userId"]

    # 处理可选字段
    if "name" in params:
        name = params["name"].strip()  # 去除前后空格
        query_params["name"] = name if name else None  # 空字符串转为None

    if "data_type" in params:
        try:
            query_params["data_type"] = int(params["data_type"])
        except (ValueError, TypeError):
            pass  # 保持None
    
    # 新增：处理 group_id 字段
    if "group_id" in params:
        try:
            # 尝试转换为整数
            group_id = int(params["group_id"])
            query_params["group_id"] = group_id
        except (ValueError, TypeError):
            # 转换失败时设置为 None
            query_params["group_id"] = None
    else:
        # 如果参数中没有提供 group_id，设置为 None
        query_params["group_id"] = None

    return query_params

# 自定义 JSON 序列化函数
def custom_json_handler(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()  # 转换为 ISO8601 格式
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# 创建全局连接池(通常在应用启动时创建)
connection_pool = pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    host='192.168.3.37',
    port=3306,
    user='root',
    password='123456',
    database='dubhe-prod'
)

def insert_dataset_n(name, data_type,uri,conver_file_uri,fail_uri,create_user_id,create_time,
                     update_time,status,data_size,data_src_size,source_file_name,remark,group_id):
    """
    使用连接池插入用户
    """
    connection = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        
        insert_query = "INSERT INTO data_dataset_n (name, data_type,uri,conver_file_uri,fail_uri,create_user_id,create_time,update_time,status,data_size,data_src_size,source_file_name,remark,group_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        print(insert_query)
        cursor.execute(insert_query, (name, data_type,uri,conver_file_uri,fail_uri,create_user_id,
                                      create_time,update_time,status,data_size,data_src_size,source_file_name,remark,group_id))
        connection.commit()
        return cursor.lastrowid
        
    except Error as e:
        print(f"插入用户 {name} 时出错: {e}")
        if connection:
            connection.rollback()
        return None
        
    finally:
        if connection:
            connection.close()  # 实




def select_data_standard_attr(record_id):
    """
    通过id查找data_attr字段的值 并将所有查到的值拼接到一起
    
    :param record_id: 要查询的记录ID
    :return: 包含所有data_attr值的列表 如 ['CoHH', 'CoHV', 'CoVH', 'CoVV', 'distance', 'phi', 'theta']
             如果查询失败或没有数据，返回空列表
    """
    connection = None
    cursor = None
    try:
        # 从连接池获取连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 执行查询
        query = "SELECT data_attr FROM data_standard_attr WHERE id = %s"
        cursor.execute(query, (record_id,))
        
        # 获取所有结果
        results = cursor.fetchall()
        
        if not results:
            print(f"未找到ID为 {record_id} 的记录")
            return []
            
        # 提取所有data_attr值并拼接
        attr_list = []
        for row in results:
            if 'data_attr' in row and row['data_attr']:
                attr_list.append(row['data_attr'])
        
        return attr_list
        
    except Error as e:
        print(f"查询ID {record_id} 的data_attr时出错: {e}")
        return []
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()  # 返回到连接池

def select_dataset_list_by_condition(query_params):
    """
    根据前端传递的参数动态查询数据集列表
    更新后的参数格式示例:
    {
        "name": "search_text",
        "data_type": 1,
        "pageNum": 2,
        "pageSize": 20,
        "userId": "admin",
        "group_id": 1   # 新增可选参数
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
        FROM data_dataset_n
        WHERE create_user_id = %(userId)s
        """
        
        # 动态构建WHERE条件
        conditions = []
        params = {
            'userId': query_params['userId'],
            'offset': (query_params['pageNum'] - 1) * query_params['pageSize'],
            'pageSize': query_params['pageSize']
        }
        
        # 添加name条件（模糊匹配）
        if query_params.get('name'):
            conditions.append("name LIKE %(name)s")
            params['name'] = f"%{query_params['name']}%"
        
        # 添加data_type条件（精确匹配）
        if query_params.get('data_type') is not None:
            conditions.append("data_type = %(data_type)s")
            params['data_type'] = query_params['data_type']
        
        # 添加group_id条件（精确匹配，可选）
        if 'group_id' in query_params and query_params['group_id'] is not None:
            conditions.append("group_id = %(group_id)s")
            params['group_id'] = query_params['group_id']
        
        # 组合完整的WHERE子句
        where_clause = base_query
        if conditions:
            where_clause += " AND " + " AND ".join(conditions)
        
        # 构建最终查询语句（包含分页）
        query = f"""
        SELECT * 
        {where_clause}
        ORDER BY id 
        LIMIT %(offset)s, %(pageSize)s;
        """
        
        # 执行查询
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 获取总数（用于分页统计）
        count_query = f"SELECT COUNT(*) AS total {where_clause};"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()['total']
        
        return {
            "records": results,
            "total": total_records,
            "pageNum": query_params['pageNum'],
            "pageSize": query_params['pageSize']
        }
        
    except Error as e:
        print(f"数据集查询出错: {e}")
        return {
            "records": [],
            "total": 0,
            "pageNum": query_params['pageNum'],
            "pageSize": query_params['pageSize']
        }
        
    finally:
        # 关闭资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def select_file_uri_by_id(id):
    """
    通过 id 查找对应的 uri（转化后的 JSON 文件绝对路径），只返回第一个结果

    :param id: 要查询的数据记录 ID
    :return: 成功返回 uri，失败或无数据返回 None
    """
    connection = None
    cursor = None
    try:
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT conver_file_uri FROM data_dataset_n WHERE id = %s"
        cursor.execute(query, (id,))
        
        result = cursor.fetchone()  # 只取一条

        if not result:
            print(f"未找到ID为 {id} 的记录")
            return None

        return result.get('conver_file_uri')

    except Exception as e:
        print(f"数据库查询出错: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def delete_dataset_by_id(id):
    """
    根据 id 删除数据记录并返回对应的 uri
    
    执行流程：
    1. 先查询 uri
    2. 如果存在记录则执行删除
    3. 返回查询到的 uri
    
    :param id: 要删除的数据记录 ID
    :return: 成功返回 uri，失败或无数据返回 None
    """
    connection = None
    cursor = None
    uri = None
    
    try:
        # 获取数据库连接
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 1. 先查询 uri
        select_query = "SELECT uri FROM data_dataset_n WHERE id = %s"
        cursor.execute(select_query, (id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"未找到ID为 {id} 的记录，无法删除")
            return None
        
        uri = result.get('uri')

        # 2. 再查询 source_file_uri
        select_query = "SELECT conver_file_uri FROM data_dataset_n WHERE id = %s"
        cursor.execute(select_query, (id,))
        result = cursor.fetchone()
        
        conver_file_uri = result.get('conver_file_uri')

        # 3. 再再查询 fail_uri
        select_query = "SELECT fail_uri FROM data_dataset_n WHERE id = %s"
        cursor.execute(select_query, (id,))
        result = cursor.fetchone()
        
        fail_uri = result.get('fail_uri')

        # 3. 执行删除操作
        delete_query = "DELETE FROM data_dataset_n WHERE id = %s"
        cursor.execute(delete_query, (id,))
        connection.commit()
        
        print(f"成功删除ID为 {id} 的记录")
        return uri,conver_file_uri,fail_uri
        
    except Exception as e:
        # 发生异常时回滚事务
        if connection:
            connection.rollback()
        print(f"删除记录时出错: {e}")
        return None
        
    finally:
        # 关闭数据库资源
        if cursor:
            cursor.close()
        if connection:
            connection.close()
if __name__ == '__main__':
    query_params = {
    "name": None,
    "data_type": None,
    "pageNum": 1,
    "pageSize": 2,
    "userId": "admin"
}
    # result = select_data_standard_attr(1)
    # print(result)  # 输出: ['CoHH', 'CoHV', 'CoVH']
    #result = select_dataset_list_by_condition(query_params)
    print(delete_dataset_by_id(8))
    # 返回结果示例
    #print(f"总记录数: {result['total']}")
    #print(f"当前页数据: {result['records']}")