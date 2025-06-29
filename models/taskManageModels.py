from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import BigInteger

db = SQLAlchemy()


# 评估任务模型 - 与您的数据库表结构匹配
class EvaluationTask(db.Model):
    __tablename__ = 'evaluate_info'  # 请替换为实际的表名
    
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