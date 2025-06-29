import os
import pymysql
from pymysql import Error

db_config = {
    'host': '192.168.3.37',
    'user': 'root',
    'password': '123456',
    'database': 'dubhe-prod'
}

def insert_data_file_n(sql_dirt):
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()

        # 构建初始插入 SQL 语句
        initial_sql = """INSERT INTO data_file_n 
        (name, status, dataset_id, file_url, create_user_id, create_time, file_type) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)"""

        cursor.execute(initial_sql, (
            sql_dirt["name"],
            sql_dirt["status"],
            sql_dirt["dataset_id"],
            sql_dirt["file_url"],
            sql_dirt["create_user_id"],
            sql_dirt["create_time"],
            sql_dirt["file_type"],
        ))
        db.commit()
    except Error as e:
        print(f"出错: {e}")
        db.rollback()
        return 404, {"error": str(e)}
    except Exception as e:
        print(f"其他错误: {e}")
        if 'db' in locals() and db.open:
            db.rollback()
        return 404, {"error": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.open:
            db.close()

def insert_data_dataset_n(sql_dirt):
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()

        # 构建初始插入 SQL 语句
        initial_sql = """INSERT INTO data_dataset_n 
        (name, data_type, uri, conver_file_uri, fail_uri, create_user_id, source_file_name,
        create_time, update_time, status, data_size, data_src_size, group_id, remark) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        cursor.execute(initial_sql, (
            sql_dirt["name"],
            sql_dirt["data_type"],
            sql_dirt["uri"],
            sql_dirt["conver_file_uri"],
            sql_dirt["fail_uri"],
            sql_dirt["create_user_id"],
            sql_dirt["source_file_name"],
            sql_dirt["create_time"],
            sql_dirt["update_time"],
            sql_dirt["status"],
            sql_dirt["data_size"],
            sql_dirt["data_src_size"],
            sql_dirt["group_id"],
            sql_dirt["remark"]
        ))
        db.commit()

        # 更新 uri 和 fail_uri
        sql_dirt["id"] = cursor.lastrowid
        sql_dirt["conver_file_uri"] = os.path.join(sql_dirt["conver_file_uri"], str(sql_dirt["id"]), "data.json")
        sql_dirt["fail_uri"] = os.path.join(sql_dirt["fail_uri"], str(sql_dirt["id"]), "data.json")

        # 构建更新 SQL 语句
        update_sql = """UPDATE data_dataset_n 
        SET conver_file_uri = %s, fail_uri = %s 
        WHERE id = %s"""

        # 执行更新操作
        cursor.execute(update_sql, (
            sql_dirt["conver_file_uri"],
            sql_dirt["fail_uri"],
            sql_dirt["id"]
        ))
        db.commit()
        return 200, sql_dirt
    except Error as e:
        print(f"出错: {e}")
        db.rollback()
        return 404, {"error": str(e)}
    except Exception as e:
        print(f"其他错误: {e}")
        if 'db' in locals() and db.open:
            db.rollback()
        return 404, {"error": str(e)}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.open:
            db.close()

def update_data_dataset_n(sql_dirt):
    try:
        # 更新数据库
        db = pymysql.connect(**db_config)
        cursor = db.cursor()
        update_sql = """UPDATE data_dataset_n 
            SET uri = %s, update_time = %s, status = %s, data_size = %s, data_src_size = %s 
            WHERE id = %s"""
        cursor.execute(update_sql, (
            sql_dirt['uri'],
            sql_dirt["update_time"],
            sql_dirt["status"],
            sql_dirt["data_size"],
            sql_dirt["data_src_size"],
            sql_dirt["id"]
        ))
        db.commit()
    except Exception as e:
        print(f"数据库保存时出错: {e}")
        if 'db' in locals() and db.open:
            db.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.open:
            db.close()

def select_data_file_n(dataset_id, label_id, page_num, page_size):
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()

        offset = (page_num - 1) * page_size

        sql = """SELECT dfn.file_url, dfn.name, dfn.status 
                 FROM data_file_n dfn
                 INNER JOIN file_label_rela flr ON dfn.file_id = flr.file_id
                 WHERE flr.dataset_id = %s AND flr.label_id = %s
                 LIMIT %s OFFSET %s"""

        cursor.execute(sql, (dataset_id, label_id, page_size, offset))
        results = cursor.fetchall()

        result_list = []
        for row in results:
            result_list.append({
                "file_url": row[0],
                "name": row[1],
                "status": row[2]
            })

        return result_list

    except Error as e:
        print(f"出错: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.open:
            db.close()

def select_data_file_n_all_labels(dataset_id, label_ids, page_num, page_size):
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()

        offset = (page_num - 1) * page_size

        placeholders = ', '.join(['%s'] * len(label_ids))
        sql = f"""SELECT dfn.file_url, dfn.name, dfn.status 
                  FROM data_file_n dfn
                  WHERE dfn.file_id IN (
                      SELECT file_id
                      FROM file_label_rela flr
                      WHERE flr.dataset_id = %s AND flr.label_id IN ({placeholders})
                      GROUP BY file_id
                      HAVING COUNT(DISTINCT flr.label_id) = %s
                  )
                  LIMIT %s OFFSET %s"""

        params = [dataset_id] + label_ids + [len(label_ids), page_size, offset]
        cursor.execute(sql, params)
        results = cursor.fetchall()

        result_list = []
        for row in results:
            result_list.append({
                "file_url": row[0],
                "name": row[1],
                "status": row[2]
            })

        return result_list

    except Error as e:
        print(f"出错: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.open:
            db.close()

def select_data_file_n_any_label(dataset_id, label_ids, page_num, page_size):
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()

        offset = (page_num - 1) * page_size

        placeholders = ', '.join(['%s'] * len(label_ids))
        sql = f"""SELECT dfn.file_url, dfn.name, dfn.status 
                  FROM data_file_n dfn
                  WHERE dfn.file_id IN (
                      SELECT file_id
                      FROM file_label_rela flr
                      WHERE flr.dataset_id = %s AND flr.label_id IN ({placeholders})
                  )
                  LIMIT %s OFFSET %s"""

        params = [dataset_id] + label_ids + [page_size, offset]
        cursor.execute(sql, params)
        results = cursor.fetchall()

        result_list = []
        for row in results:
            result_list.append({
                "file_url": row[0],
                "name": row[1],
                "status": row[2]
            })

        return result_list

    except Error as e:
        print(f"出错: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.open:
            db.close()