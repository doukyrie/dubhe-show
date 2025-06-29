import json
from flask import Blueprint, Response, request, jsonify

from mysql_1 import custom_json_handler, parse_query_params, select_dataset_list_by_condition
from mysql_datasetfile import parse_query_params_datasetfile, select_datasetfile_list_by_condition

# 创建蓝图 (URL前缀为 /api/dataset)
bp3 = Blueprint('dataset', __name__, url_prefix='/api/datasetfile')