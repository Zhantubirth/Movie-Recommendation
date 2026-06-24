#The author of all functions in this module:Yaohang Zhong
from peewee import MySQLDatabase

# 创建数据库连接实例，
# Create a database connection instance，
# Contain specific information about the database to be connected to
db = MySQLDatabase(
    'movie_recommendation',
    user='root',
    password='Zqy762131',
    host='localhost',
    port=3306
)
# 封装了一个获取数据库连接的函数，其他模块可以调用来拿到连接对象
# A helper function to get the db connection, other modules can call this
def get_db_connection():
    return db.connection()
