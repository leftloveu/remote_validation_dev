import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量
# username = os.environ.get("MYSQL_USERNAME", 'root')
# password = os.environ.get("MYSQL_PASSWORD", 'kqSJ9b7J')
# db_address = os.environ.get("MYSQL_ADDRESS", 'sh-cynosdbmysql-grp-hsc16e2c.sql.tencentcdb.com')
# port = os.environ.get("MYSQL_PORT", 22114)
# database = os.environ.get("MYSQL_DATABASE", 'flask_demo')

username    = 'root'
password    = 'kqSJ9b7J'
db_address  = '10.26.104.118'
port        = 3306
database    = 'remote_validation'
# 10.26.104.118:3306