from datetime import datetime
import json
import os
import shutil
from flask import Blueprint, Response, request, jsonify
from pymysql import MySQLError

from mysql_1 import custom_json_handler, parse_query_params, select_dataset_list_by_condition
from mysql_datasetfile import make_dataset, merge_dataset, parse_query_params_datasetfile, select_datasetfile_list_by_condition

# 创建蓝图 (URL前缀为 /api/dataset)
bp = Blueprint('dataset', __name__, url_prefix='/api/datasetfile')



# 示例接口：GET 请求返回数据
@bp.route('/list', methods=['GET'])
def get_datasetfile_list():
    res = request.args

    query_params = parse_query_params_datasetfile(res)
    print(query_params)
    ans = select_datasetfile_list_by_condition(query_params)
    return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            "data": ans['records'],
            "total":ans['total'],
            "total_counts": ans['total_counts'],
        }, default=custom_json_handler, ensure_ascii=False),
        mimetype='application/json'
    )

@bp.route('/make_dataset', methods=['GET'])
def make_dataset_api():
    res = request.args

    query_params = parse_query_params_datasetfile(res)
    print(query_params)
    ans = select_datasetfile_list_by_condition(query_params)
    result = ans['records']
    make_dataset(res,result)

    return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            "data": ans['records'],
            "total":ans['total'],
            "total_counts": ans['total_counts'],
        }, default=custom_json_handler, ensure_ascii=False),
        mimetype='application/json'
    )

@bp.route('/merge_dataset', methods=['GET'])
def merge_dataset_api():
    res = request.args

    query_params = parse_query_params_datasetfile(res)
    print(query_params)
    ans = select_datasetfile_list_by_condition(query_params)
    result = ans['records']
    merge_dataset(res,result)

    return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            "data": ans['records'],
            "total":ans['total'],
            "total_counts": ans['total_counts'],
        }, default=custom_json_handler, ensure_ascii=False),
        mimetype='application/json'
    )