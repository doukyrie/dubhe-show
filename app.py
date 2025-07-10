from flask import Flask
from models.models import db
from evaluateTaskManage.taskManage import bp as task_manage_bp
from evaluateTaskManage.taskDetail import bp as task_detail_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@192.168.3.6:30678/dubhe-prod'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(task_manage_bp)
    app.register_blueprint(task_detail_bp)
    
    # 添加CORS（如果需要）
    
    CORS(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='192.168.3.5')