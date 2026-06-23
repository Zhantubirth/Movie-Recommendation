#The author of all functions in this module:Yaohang Zhong
import pymysql
from peewee import MySQLDatabase

db = MySQLDatabase(
    'movie_recommendation', # 数据库名
    user='root',
    password='Zqy762131',
    host='localhost',
    port=3306
)

def get_db_connection():
    """返回数据库连接对象"""
    return db.connection()
