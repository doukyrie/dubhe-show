import datetime
import multiprocessing
import shutil
import uuid
from flask import Flask, Response, abort, request, jsonify, send_file
from flask_cors import CORS
import cv2
from mysql_1 import custom_json_handler, delete_dataset_by_id, parse_query_params, select_dataset_list_by_condition, select_file_uri_by_id
from process_mat_zip import process_mat_zip
from api_dataset_file import bp as datasetfile_bp
from label_group import bp1 as labelgroup_bp
from label import bp2 as label_bp
from flask import Flask, request, render_template, jsonify
import util
import database
import zipfile
import os
import scipy.io
import json
import numpy as np


app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求（开发环境可用）



UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/dataset/upload_image', methods=['POST'])
def upload_image_file():
    # 写死data_type 和 create_user_id, 后续修改更改这里
    data_type = 3
    create_user_id = "admin"

    if 'file' not in request.files:
        dataset_name = request.files.name
        return jsonify({"error": "没有文件上传"}), 400

    f = request.files['file']
    dataset_name = request.form['name']
    group_id = request.form['group_id']

    if f.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if not f.filename.lower().endswith('.zip'):
        return jsonify({"error": "只允许上传 .zip 格式文件"}), 400

    unique_id = str(uuid.uuid4())

    save_dir = os.path.join(UPLOAD_FOLDER, f"{123}_{unique_id}")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    zip_path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(zip_path)
    print(request)
    print(dataset_name)
    
    source_file_name = f.filename
    name =  os.path.splitext(source_file_name)[0]

    if data_type is None and create_user_id is None:
        return jsonify({"message": "上传失败, 缺少参数"}), 400

    sql_dirt = {
        "name": name, 
        "data_type": data_type,
        "uri": os.path.join(os.path.abspath(f"./dataset/src"), data_type),
        "conver_file_uri": os.path.abspath(f"./dataset/result"),
        "fail_uri": os.path.abspath(f"./dataset/result"),
        "create_user_id": create_user_id,
        "source_file_name": source_file_name,
        "status": 1,
        "create_time": datetime.datetime.now(),
        "update_time": datetime.datetime.now(),
        "data_size": 0,
        "data_src_size": 0,
        "remark": '',
        "group_id": group_id,
        "save_path": zip_path
    }
    code, sql_dirt = database.insert_data_dataset_n(sql_dirt)

    # 如果 code 为 404, 返回上传失败
    if code == 404:
        return jsonify({"message": "上传失败，数据库操作错误"}), 404
    # 如果 code 为 200, 返回上传成功
    # 启动新进程处理读取和解压
    process = multiprocessing.Process(target=util.process_zip_file, args=(sql_dirt,))
    process.start()

    return jsonify({
        'status': 'success'
    })

@app.route('/api/dataset/upload_video', methods=['POST'])
def upload_video_file():
    # 写死data_type 和 create_user_id, 后续修改更改这里
    data_type = 4
    create_user_id = "admin"

    if 'file' not in request.files:
        dataset_name = request.files.name
        return jsonify({"error": "没有文件上传"}), 400

    f = request.files['file']
    dataset_name = request.form['name']
    group_id = request.form['group_id']

    if f.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if not f.filename.lower().endswith('.zip'):
        return jsonify({"error": "只允许上传 .zip 格式文件"}), 400

    unique_id = str(uuid.uuid4())

    save_dir = os.path.join(UPLOAD_FOLDER, f"{123}_{unique_id}")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    zip_path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(zip_path)
    print(request)
    print(dataset_name)
    
    source_file_name = f.filename
    name =  os.path.splitext(source_file_name)[0]

    if data_type is None and create_user_id is None:
        return jsonify({"message": "上传失败, 缺少参数"}), 400

    sql_dirt = {
        "name": name, 
        "data_type": data_type,
        "uri": os.path.join(os.path.abspath(f"./dataset/src"), data_type),
        "conver_file_uri": os.path.abspath(f"./dataset/result"),
        "fail_uri": os.path.abspath(f"./dataset/result"),
        "create_user_id": create_user_id,
        "source_file_name": source_file_name,
        "status": 1,
        "create_time": datetime.datetime.now(),
        "update_time": datetime.datetime.now(),
        "data_size": 0,
        "data_src_size": 0,
        "group_id": group_id,
        "remark": '',
        "save_path": zip_path
    }
    code, sql_dirt = database.insert_data_dataset_n(sql_dirt)

    # 如果 code 为 404, 返回上传失败
    if code == 404:
        return jsonify({"message": "上传失败，数据库操作错误"}), 404
    # 如果 code 为 200, 返回上传成功
    # 启动新进程处理读取和解压
    process = multiprocessing.Process(target=util.process_zip_file, args=(sql_dirt,))
    process.start()

    return jsonify({
        'status': 'success'
    })

# 示例接口：接收 POST 请求
@app.route('/api/dataset/upload', methods=['POST'])
def login():
    
    # 1. 获取上传的文件
    if 'file' not in request.files:
        dataset_name = request.files.name
        return jsonify({"error": "没有文件上传"}), 400

    file = request.files['file']
    dataset_name = request.form['name']
    group_id = request.form['group_id']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if not file.filename.lower().endswith('.zip'):
        return jsonify({"error": "只允许上传 .zip 格式文件"}), 400

    # 2. 保存上传的 ZIP 文件
    unique_id = str(uuid.uuid4())
    
    save_dir = os.path.join(UPLOAD_FOLDER, f"{123}_{unique_id}")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(zip_path)
    print(request)
    print(dataset_name)
    process_mat_zip(dataset_name,zip_path,group_id)
    return jsonify({
            'status': 'success'
        })

# 示例接口：GET 请求返回数据
@app.route('/api/dataset/list', methods=['GET'])
def get_data():
    res = request.args

    query_params = parse_query_params(res)
    print(query_params)
    ans = select_dataset_list_by_condition(query_params)
    return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            "data": ans['records'],
            "total":ans['total']
        }, default=custom_json_handler, ensure_ascii=False),
        mimetype='application/json'
    )


@app.route('/api/dataset/delete/<id>', methods=['DELETE'])
def delete_file(id):
    """
    数据集删除接口
    1. 删除数据库记录并获取文件路径
    2. 删除对应的物理文件
    3. 返回操作结果
    
    :param id: 要删除的数据集ID
    :return: JSON响应
    """
    try:
        # 1. 删除数据库记录并获取文件路径
        uri,conver_file_uri,fail_uri = delete_dataset_by_id(id)
        
        if None in (uri, conver_file_uri, fail_uri):
            abort(404, description="数据库记录不存在")
        
        # 安全验证：确保路径存在（可以是文件或目录）
        if not os.path.exists(uri):
            abort(400, description="无效的路径")
        
    # 2. 删除物理文件/目录
        try:
            # 如果是目录，递归删除
            if os.path.isdir(uri):
                shutil.rmtree(uri)
            else:
                os.remove(uri)
            
            # 删除其他文件（假设这些是单独的文件）
            if os.path.exists(conver_file_uri):
                os.remove(conver_file_uri)
            if os.path.exists(fail_uri):
                os.remove(fail_uri)
                
        except PermissionError:
            abort(403, description="没有删除权限")
        except Exception as e:
            abort(500, description=f"删除失败: {str(e)}")
        
        # 3. 返回成功响应
        return jsonify({
            "success": True,
            "code": 200,
            "message": "删除成功",
            "data": {
                "deleted_file": conver_file_uri
            }
        })
        
    except Exception as e:
        # 捕获其他未处理的异常
        abort(500, description=f"服务器错误: {str(e)}")
    
 

@app.route('/api/dataset/download/<id>', methods=['GET'])
def download_file(id):
    """
    文件下载接口
    :param id: 要下载的id
    :return: 文件下载响应
    """
    try:
        # 构建文件路径

        file_path = select_file_uri_by_id(id)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            abort(404, description="File not found")
            
        # 发送文件
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        abort(500, description=str(e))




# 注册蓝图
app.register_blueprint(datasetfile_bp)
app.register_blueprint(labelgroup_bp)
app.register_blueprint(label_bp)

if __name__ == '__main__':
    #process_mat_zip('data1.zip')
    app.run(host='192.168.3.5')