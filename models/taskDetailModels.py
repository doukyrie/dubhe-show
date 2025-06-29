from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import BigInteger

db = SQLAlchemy()

# 模型定义保持不变
class PtTrainAlgorithm(db.Model):
    __tablename__ = 'pt_train_algorithm'
    id = db.Column(db.Integer, primary_key=True)
    algorithm_name = db.Column(db.String(100))
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)

class PtImage(db.Model):
    __tablename__ = 'pt_image'
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(100))
    image_tag = db.Column(db.String(50))
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)

class DataDataset(db.Model):
    __tablename__ = 'data_dataset'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)

class PtModelInfo(db.Model):
    __tablename__ = 'pt_model_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    model_version = db.Column(BigInteger)
    origin_user_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer)

class PtModelBranch(db.Model):
    __tablename__ = 'pt_model_branch'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(BigInteger)
    version = db.Column(db.String(8))
    deleted = db.Column(db.Integer)


class ResourceSpecs(db.Model):
    __tablename__ = 'resource_specs'
    id = db.Column(db.Integer, primary_key=True)
    specs_name = db.Column(db.String(100))
    resources_pool_type = db.Column(db.String(50))
    module = db.Column(db.Integer)
    deleted = db.Column(db.Integer)

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
