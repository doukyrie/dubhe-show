import json
from flask import Blueprint, Response, request, jsonify

from mysql_1 import custom_json_handler, parse_query_params, select_dataset_list_by_condition
from mysql_datasetfile import parse_query_params_datasetfile, select_datasetfile_list_by_condition
from mysql_label_group import insert_label_group_info, parse_query_params_label_group, select_label_group_list_by_condition

# 创建蓝图 (URL前缀为 /api/dataset)
bp1 = Blueprint('labelgroup', __name__, url_prefix='/label/group')

# 示例接口：GET 请求返回数据
@bp1.route('/create', methods=['POST'])
def create_label_group():
        res = request.data
        insert_label_group_info(res)
        return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            
        }),
        mimetype='application/json'
    )

# 示例接口：GET 请求返回数据
@bp1.route('/list', methods=['GET'])
def list_label_group():
        res = request.args
        query = parse_query_params_label_group(res)
        ans = select_label_group_list_by_condition(query)
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