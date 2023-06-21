from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
# import MySQLdb

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True, template_folder='templates', static_folder='static')
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['DEBUG'] = config.DEBUG

# 设定数据库链接


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}:{}/flask_demo'.format(config.username, config.password,
                                                                             config.db_address, config.port)
# print(app.config['SQLALCHEMY_DATABASE_URI'])
print('看看能不能打印到控制台')
# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载控制器
from wxcloudrun import views

# 加载配置
app.config.from_object('config')

# conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8', cursorclass=pymysql.cursors.DictCursor)
# print(conn)
# conn.close()
# print('conn closed')

# pymysql_conn = pymysql.connect(host=config.db_address, user=config.username, password=config.password, db=config.database, port=config.port, charset='utf8')

# def get_conn():
#     conn = None
#     try:
#         conn = pymysql.connect(host=config.db_address, user=config.username, password=config.password, db=config.database, port=config.port, charset='utf8')
#     except Exception as e:
#         print(str(e))
#     finally:
#         return conn
