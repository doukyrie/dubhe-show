from flask import Flask, request, jsonify, Blueprint
from models.models import db, EvaluationTask, EvaluateDetail


bp = Blueprint('taskManage', __name__, url_prefix='/api/taskManage')



@bp.route('/createTask', methods=['POST'])
def add_task():
    data = request.json
    
    # 验证输入数据
    if not data or 'evaluateName' not in data or 'evaluateCnt' not in data or 'createUserId' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数: evaluateName, evaluateCnt或createUserId'}), 400
    
    try:
        # 创建新任务（主表）
        new_task = EvaluationTask(
            evaluate_name=data['evaluateName'],
            evaluate_cnt=int(data['evaluateCnt']),
            evaluate_status=data.get('evaluateStatus', '0'),
            create_user_id=data['createUserId']  # 直接使用前端传入的createUserId
        )
        
        db.session.add(new_task)
        db.session.flush()  # 先获取ID但不提交事务
        
        # 获取生成的主表ID
        evaluate_id = new_task.evaluate_id
        task_count = int(data['evaluateCnt'])
        create_user_id = data['createUserId']  # 获取前端传入的createUserId
        
        # 创建明细数据（格式：主ID-序号）
        detail_records = []
        for i in range(1, task_count + 1):
            detail_records.append({
                'evaluate_id': evaluate_id,
                'evaluate_train_id': f"{evaluate_id}-{i}",  # 字符串格式
                'create_user_id': create_user_id  # 添加create_user_id到明细表
            })
        
        # 批量插入明细数据
        if detail_records:
            db.session.execute(
                EvaluateDetail.__table__.insert(),
                detail_records
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            "code": 200, 
            'data': {
                'evaluateId': evaluate_id,
                'detailCount': task_count,
                'detailIds': [record['evaluate_train_id'] for record in detail_records],
                **new_task.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'创建任务失败: {str(e)}'
        }), 500
    finally:
        db.session.close()



@bp.route('/getTask', methods=['GET'])
def get_tasks():
    try:
        # 获取前端传入的userId参数
        user_id = request.args.get('createUserId')
        
        # 校验userId必须提供
        if not user_id:
            return jsonify({'success': False, 'message': '必须提供userId参数'}), 400

        # 查询create_user_id等于userId的任务，并按评估时间降序排列
        tasks = EvaluationTask.query.filter(
            EvaluationTask.create_user_id == user_id
        ).order_by(
            EvaluationTask.evaluate_time.desc()
        ).all()
        
        return jsonify({
            'success': True,
            'data': [task.to_dict() for task in tasks]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取任务列表失败: {str(e)}'}), 500
    finally:
        db.session.close()
    

@bp.route('/queryTask', methods=['POST'])
def query_tasks():
    try:
        data = request.json
        
        # 获取分页参数（新命名）
        pageNum = data.get('pageNum', 1)      # 原page
        pageSize = data.get('pageSize', 10)   # 原per_page
        
        # 参数校验
        pageNum = max(1, int(pageNum))
        pageSize = min(max(1, int(pageSize)), 100)

        # 查询条件（新命名）
        evaluateName = data.get('evaluateName', '').strip()    # 原evaluate_name
        evaluateStatus = data.get('evaluateStatus')           # 原evaluate_status
        createUserId = data.get('createUserId')             # 新增的创建用户ID
        
        # 必须提供create_user_id
        if not createUserId:
            return jsonify({'success': False, 'message': '必须提供create_user_id参数'}), 400

        query = EvaluationTask.query.filter(EvaluationTask.create_user_id == createUserId)
        
        # 模糊查询条件
        if evaluateName:
            query = query.filter(EvaluationTask.evaluate_name.like(f'%{evaluateName}%'))
        
        # 状态查询条件
        if evaluateStatus:
            query = query.filter(EvaluationTask.evaluate_status == evaluateStatus)

        # 分页查询
        pagination = query.order_by(EvaluationTask.evaluate_time.desc()).paginate(
            page=pageNum,        # 使用新参数名
            per_page=pageSize,   # 使用新参数名
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [task.to_dict() for task in pagination.items],
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'currentPage': pagination.page,    # 响应也改为驼峰
                'pageSize': pagination.per_page,    # 响应也改为驼峰
                'hasNext': pagination.has_next,     # 响应也改为驼峰
                'hasPrev': pagination.has_prev      # 响应也改为驼峰
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500
    finally:
        db.session.close()



#删除功能
# 批量删除接口
@bp.route('/deleteTask', methods=['DELETE'])
def batch_delete_tasks():
    try:
        data = request.json
        task_ids = data.get('ids', [])
        
        if not task_ids:
            return jsonify({'success': False, 'message': '请选择要删除的任务'}), 400

        # 开启事务
        db.session.begin()

        # 1. 删除明细表数据（直接使用明细表的 create_user_id 过滤）
        deleted_details = EvaluateDetail.query.filter(
            EvaluateDetail.evaluate_id.in_(task_ids),
        ).delete(synchronize_session=False)

        # 2. 删除主表数据（仍然使用主表的 create_user_id 过滤）
        deleted_tasks = EvaluationTask.query.filter(
            EvaluationTask.evaluate_id.in_(task_ids),
        ).delete(synchronize_session=False)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_tasks} 条主任务和 {deleted_details} 条明细记录'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量删除失败: {str(e)}'
        }), 500
    finally:
        db.session.close()