from datetime import datetime
from sqlalchemy import BigInteger
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# 模型定义保持不变
class PtTrainAlgorithm(db.Model):
    __tablename__ = 'pt_train_algorithm'
    id = db.Column(db.Integer, primary_key=True)
    algorithm_name = db.Column(db.String(100))
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)
    create_user_id = db.Column(db.String(100))

class PtImage(db.Model):
    __tablename__ = 'pt_image'
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(100))
    image_tag = db.Column(db.String(50))
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)
    create_user_id = db.Column(db.String(100))

class DataDataset(db.Model):
    __tablename__ = 'data_dataset'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    type = db.Column(db.Integer)
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)
    uri = db.Column(db.String(100))
    deleted = db.Column(db.Integer)
    create_user_id = db.Column(db.String(100))

class PtModelInfo(db.Model):
    __tablename__ = 'pt_model_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    model_version = db.Column(BigInteger)
    origin_user_id = db.Column(db.Integer)
    model_resource = db.Column(db.Integer)
    deleted = db.Column(db.Integer)
    create_user_id = db.Column(db.String(100))

class PtModelBranch(db.Model):
    __tablename__ = 'pt_model_branch'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(BigInteger)
    version = db.Column(db.String(8))
    deleted = db.Column(db.Integer)
    create_user_id = db.Column(db.String(100))


class ResourceSpecs(db.Model):
    __tablename__ = 'resource_specs'
    id = db.Column(db.Integer, primary_key=True)
    specs_name = db.Column(db.String(100))
    resources_pool_type = db.Column(db.String(50))
    module = db.Column(db.Integer)
    deleted = db.Column(db.Integer)
    cpu_num = db.Column(db.Integer)
    gpu_num = db.Column(db.Integer)
    mem_num = db.Column(db.Integer)
    workspace_request = db.Column(db.Integer)
    create_user_id = db.Column(db.String(100))


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    deleted = db.Column(db.Integer)

class EvaluateDetail(db.Model):
    __tablename__ = 'evaluate_detail'
    __table_args__ = (
        db.PrimaryKeyConstraint('evaluate_id', 'evaluate_train_id'),
    )
    
    evaluate_id = db.Column(BigInteger, nullable=False)
    evaluate_train_id = db.Column(db.String(50), nullable=False)
    train_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    algorithm_id = db.Column(BigInteger)
    image_tag = db.Column(db.String(255))
    image_id = db.Column(BigInteger)
    data_source_id = db.Column(BigInteger)
    run_command = db.Column(db.Text)
    resources_id = db.Column(BigInteger)
    model_id = db.Column(BigInteger)
    model_branch_id = db.Column(BigInteger)
    create_time = db.Column(db.DateTime, default=datetime.now)
    create_user_id = db.Column(db.String(100))


# 评估任务模型 - 与您的数据库表结构匹配
class EvaluationTask(db.Model):
    __tablename__ = 'evaluate_info'
    
    evaluate_id = db.Column(BigInteger, primary_key=True, autoincrement=True, comment='评估任务id')
    evaluate_name = db.Column(db.String(100), nullable=False, comment='评估任务名称')
    evaluate_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    evaluate_status = db.Column(db.String(100), nullable=False, default='0', comment='评估状态')
    evaluate_cnt = db.Column(db.Integer, nullable=False, comment='任务数量')
    create_user_id = db.Column(db.String(100), comment='创建人')

    
    def to_dict(self):
        return {
            'evaluateId': self.evaluate_id,  # 原 evaluate_id
            'evaluateName': self.evaluate_name,  # 原 evaluate_name
            'evaluateTime': self.evaluate_time.strftime('%Y-%m-%d %H:%M:%S') if self.evaluate_time else None,  # 原 evaluate_time
            'evaluateStatus': self.evaluate_status,  # 原 evaluate_status
            'evaluateCnt': self.evaluate_cnt,  # 原 evaluate_cnt
            'createUserId': self.create_user_id  # 原 create_user_id
        }