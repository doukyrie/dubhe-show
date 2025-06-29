import json
from flask import Blueprint, Response, request, jsonify

from mysql_1 import custom_json_handler
from mysql_label_group import  insert_file_label_rela_and_update_status, insert_label_info, parse_query_params_label_group, parse_query_params_label_list, select_label_group_list_by_condition, select_label_list_by_group_id


# 创建蓝图 (URL前缀为 /api/dataset)
bp2 = Blueprint('labelg', __name__, url_prefix='/label')


# 示例接口：GET 请求返回数据
@bp2.route('/create', methods=['POST'])
def create_label_group():
        res = request.data
        insert_label_info(res)
        return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            
        }),
        mimetype='application/json'
    )

# 示例接口：GET 请求返回数据
@bp2.route('/list', methods=['GET'])
def list_label_group():
        res = request.args
        query = parse_query_params_label_list(res)
        ans = select_label_list_by_group_id(query)
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


#将传过来的文件打上对应标签
@bp2.route('/set_label', methods=['POST'])
def set_label():
        res = request.data
        insert_file_label_rela_and_update_status(res)
        return Response(
        json.dumps({
            "success": True,
            "code": 200,
            "message": "操作成功",
            
        }),
        mimetype='application/json'
    )