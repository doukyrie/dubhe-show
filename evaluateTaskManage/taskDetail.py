from flask import Flask, request, jsonify,Blueprint
from models.models import db, EvaluateDetail, PtTrainAlgorithm, PtImage, DataDataset, PtModelInfo, ResourceSpecs, User,PtModelBranch
import requests

bp = Blueprint('taskDetail', __name__, url_prefix='/api/taskDetail')

# Java后端API地址
JAVA_API_URL = "http://192.168.3.25:30800/api/v1/train/trainJob"


@bp.route('/getTaskDetail', methods=['GET'])
def get_task_details():
    try:
        # 获取查询参数
        current_evaluate_id = request.args.get('evaluateId', type=int)
        if not current_evaluate_id:
            return jsonify({'success': False, 'message': 'evaluateId is required'}), 400

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # 构建查询 - 只查询匹配evaluate_id的记录
        query = EvaluateDetail.query.filter_by(evaluate_id=current_evaluate_id)

        # 执行分页查询
        pagination = query.order_by(EvaluateDetail.evaluate_train_id).paginate(
            page=page, 
            per_page=per_page,
            error_out=False
        )

        # 构建响应数据（驼峰式）
        details = []
        for detail in pagination.items:
            details.append({
                'evaluateId': detail.evaluate_id,
                'evaluateTrainId': detail.evaluate_train_id,
                'trainName': detail.train_name,
                'description': detail.description,
                'algorithmId': detail.algorithm_id,
                'imageTag': detail.image_tag,
                'imageId': detail.image_id,
                'dataSourceId': detail.data_source_id,
                'runCommand': detail.run_command,
                'resourcesId': detail.resources_id,
                'modelId': detail.model_id,
                'modelBranchId': detail.model_branch_id,
                'createTime': detail.create_time if detail.create_time is None else detail.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'createUserId': detail.create_user_id,
            })

        return jsonify({
            'success': True,
            'data': details,
            'pagination': {
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'currentPage': pagination.page,
                    'perPage': pagination.per_page
                }
        })
    

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    finally:
        db.session.close()



@bp.route('/getSelData', methods=['GET'])
def get_all_resources():
    try:
        # 获取当前用户名
        current_username = request.args.get('username')
        if not current_username:
            return jsonify({"success": False, "message": "未提供用户名"}), 401

        # 查询当前用户ID
        user = User.query.filter_by(username=current_username).first()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        current_user_id = user.id

        # 1. 查询算法数据
        algorithms = PtTrainAlgorithm.query.filter(
            ((PtTrainAlgorithm.origin_user_id == 0) | 
            (PtTrainAlgorithm.origin_user_id == current_user_id)) &
            (PtTrainAlgorithm.deleted == 0)
        ).all()

        # 2. 查询镜像数据
        images = PtImage.query.filter(
            ((PtImage.origin_user_id == 0) | 
            (PtImage.origin_user_id == current_user_id)) &
            (PtImage.deleted == 0)
        ).all()

        # 3. 查询数据集
        datasets = DataDataset.query.filter(
            (DataDataset.origin_user_id == current_user_id) &
            (DataDataset.deleted == 0)
        ).all()

        # 4. 查询模型和对应的分支版本
        models = PtModelInfo.query.filter(
            (PtModelInfo.origin_user_id == current_user_id) &
            (PtModelInfo.deleted == 0)
        ).all()
        
        # 获取每个模型的所有分支版本
        model_data = []
        for model in models:
            branches = PtModelBranch.query.filter(
                (PtModelBranch.parent_id == model.id) &
                (PtModelBranch.deleted == 0)
            ).all()
            
            versions = [branch.version for branch in branches]
            
            model_data.append({
                "id": model.id,
                "name": model.name,
                "modelBranchId": versions  # 现在是一个数组
            })

        # 5. 查询资源规格
        resources = ResourceSpecs.query.filter(
            (ResourceSpecs.module == 2) &
            (ResourceSpecs.deleted == 0)
        ).all()

        # 构建响应数据
        result = {
            "algorithm": [{
                "id": algo.id,
                "algorithmName": algo.algorithm_name
            } for algo in algorithms],
            
            "image": [{
                "id": img.id,
                "imageName": img.image_name,
                "imageTag": img.image_tag
            } for img in images],
            
            "dataset": [{
                "id": ds.id,
                "name": ds.name
            } for ds in datasets],
            
            "model": model_data,  # 使用处理后的模型数据
            
            "resource": [{
                "id": res.id,
                "specsName": res.specs_name,
                "resourcesPoolType": res.resources_pool_type
            } for res in resources]
        }

        return jsonify({"success": True, "data": result})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.session.close()
    


@bp.route('/updateTaskDetail', methods=['POST'])
def update_task_detail():
    data = request.json
    
    # 验证必要参数
    if not data or 'evaluateId' not in data or 'evaluateTrainId' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数: evaluateId和evaluateTrainId'}), 400

    try:
        # 根据复合主键查找记录
        detail = EvaluateDetail.query.filter_by(
            evaluate_id=data['evaluateId'],
            evaluate_train_id=data['evaluateTrainId']
        ).first()

        if not detail:
            return jsonify({'success': False, 'message': '未找到匹配的任务明细记录'}), 404

        # 更新可修改字段（排除主键和创建时间等不可变字段）
        updatable_fields = {
            'train_name': 'trainName',
            'description': 'description',
            'algorithm_id': 'algorithmId',
            'image_tag': 'imageTag',
            'image_id': 'imageId',
            'data_source_id': 'dataSourceId',
            'run_command': 'runCommand',
            'resources_id': 'resourcesId',
            'model_id': 'modelId',
            'model_branch_id': 'modelBranchId',
        }

        for db_field, json_field in updatable_fields.items():
            if json_field in data:
                setattr(detail, db_field, data[json_field])

        # 添加更新时间戳（如果模型中有这个字段）
        #if hasattr(detail, 'update_time'):
            #detail.update_time = datetime.now()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': {
                'evaluateId': detail.evaluate_id,
                'evaluateTrainId': detail.evaluate_train_id,
                'updatedFields': list(updatable_fields.keys())
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'更新任务明细失败: {str(e)}'
        }), 500
    finally:
        db.session.close()
    


@bp.route('/submitTaskDetail', methods=['POST'])
def submit_task_detail():
    try:
        data_list = request.json
        if not isinstance(data_list, list):
            return jsonify({"success": False, "message": "请求数据应为JSON数组"}), 400

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "message": "缺少Authorization Token"}), 401

        java_request_data_list = []
        errors = []
        success_count = 0

        for data in data_list:
            try:
                # 验证必要字段
                required_fields = ['evaluateId', 'evaluateTrainId', 'createUserId',
                                 'resourcesId', 'dataSourceId', 'imageId', 'algorithmId',
                                 'modelId', 'modelBranchId']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 缺少必要字段 {', '.join(missing_fields)}")
                    continue

                # 1. 先查询是否已存在记录
                evaluate_detail = EvaluateDetail.query.filter_by(
                    evaluate_id=data['evaluateId'],
                    evaluate_train_id=data['evaluateTrainId'],
                    #create_user_id=data['createUserId']
                ).first()

                if not evaluate_detail:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到对应的评估详情记录")
                    continue

                # 2. 查询关联数据
                resource = ResourceSpecs.query.filter_by(
                    id=data['resourcesId'],
                    deleted=0,
                    #create_user_id=data['createUserId']
                ).first()
                if not resource:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到资源规格")
                    continue

                dataset = DataDataset.query.filter_by(
                    id=data['dataSourceId'],
                    deleted=0,
                    create_user_id=data['createUserId']
                ).first()
                if not dataset:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到数据集")
                    continue

                image = PtImage.query.filter_by(
                    id=data['imageId'],
                    deleted=0,
                    create_user_id=data['createUserId']
                ).first()
                if not image:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到镜像")
                    continue

                algorithm = PtTrainAlgorithm.query.filter_by(
                    id=data['algorithmId'],
                    deleted=0,
                    create_user_id=data['createUserId']
                ).first()
                if not algorithm:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到算法")
                    continue

                modelInfo = PtModelInfo.query.filter_by(
                    id=data['modelId'],
                    deleted=0,
                    create_user_id=data['createUserId']
                ).first()
                if not modelInfo:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到模型")
                    continue

                modelBranch = PtModelBranch.query.filter_by(
                    parent_id=data['modelId'],
                    version=data['modelBranchId'],
                    deleted=0,
                    #create_user_id=data['createUserId']
                ).first()
                if not modelBranch:
                    errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 未找到模型分支")
                    continue
                
                db.session.add(evaluate_detail)
                # 3. 更新现有记录
                evaluate_detail.train_name = data.get('trainName')
                evaluate_detail.description = data.get('description')
                evaluate_detail.algorithm_id = data['algorithmId']
                evaluate_detail.image_tag = image.image_tag
                evaluate_detail.image_id = data['imageId']
                evaluate_detail.data_source_id = data['dataSourceId']
                evaluate_detail.run_command = data.get('runCommand')
                evaluate_detail.resources_id = data['resourcesId']
                evaluate_detail.model_id = data['modelId']
                evaluate_detail.model_branch_id = data['modelBranchId']


                # 4. 构建Java请求数据
                java_request_data = {
                    "id": None,
                    "trainName": data.get('trainName'),
                    "jobName": None,
                    "paramName": None,
                    "description": data.get('description'),
                    "algorithmId": data['algorithmId'],
                    "algorithmName": algorithm.algorithm_name,
                    "datasetType": dataset.type,
                    "imageTag": image.image_tag,
                    "imageName": image.image_name,
                    "notebookId": None,
                    "dataSourceName": dataset.name,
                    "dataSourceId": data['dataSourceId'],
                    "dataSourcePath": dataset.uri,
                    "runCommand": data.get('runCommand'),
                    "runParams": {},
                    "trainType": 0,
                    "valType": 0,
                    "resourcesPoolNode": 1,
                    "resourcesPoolType": resource.resources_pool_type,
                    "trainJobSpecsName": resource.specs_name,
                    "outPath": "/home/result/",
                    "logPath": "/home/log/",
                    "delayCreateTime": 0,
                    "delayDeleteTime": 0,
                    "modelResource": modelInfo.model_resource,
                    "modelId": data['modelId'],
                    "modelBranchId": modelBranch.id,
                    "runParamsNameMap": {},
                    "ptDdrlTrainParam": {
                        "scenario": None,
                        "distributed": False
                    },
                    "cpuNum": resource.cpu_num,
                    "gpuNum": resource.gpu_num,
                    "memNum": resource.mem_num,
                    "workspaceRequest": resource.workspace_request
                }

                java_request_data_list.append(java_request_data)
                success_count += 1

            except Exception as e:
                db.session.rollback()
                errors.append(f"记录{data.get('evaluateTrainId', '未知')}: 处理错误 - {str(e)}")
                continue

        db.session.commit()

        if not java_request_data_list:
            return jsonify({
                "success": False,
                "message": "所有记录处理失败",
                "errors": errors
            }), 400

        headers = {'Content-Type': 'application/json', 'Authorization': auth_header}
        response = requests.post(JAVA_API_URL, json=java_request_data_list, headers=headers, timeout=10)

        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": f"成功更新{success_count}条记录并提交到Java后端",
                "java_response": response.json(),
                "errors": errors if errors else None
            })
        else:
            db.session.rollback()
            return jsonify({
                "success": False,
                "message": f"Java后端错误: {response.status_code}",
                "response_text": response.text,
                "errors": errors
            }), response.status_code

    except requests.exceptions.Timeout:
        db.session.rollback()
        return jsonify({"success": False, "message": "连接Java后端超时"}), 504
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.session.close()