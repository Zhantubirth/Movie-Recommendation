#The author of all functions in this module:Yaohang Zhong
from peewee import *
from datetime import datetime
from .database import db

# 所有模型都继承 BaseModel，指定所有表都用这个数据库连接
# All models inherit BaseModel, specifying that all tables use this database connection
class BaseModel(Model):
    class Meta:
        database = db

# 对应数据库中的 user 表，存储用户账号信息
# Maps to the 'user' table in database, stores user account info
class User(BaseModel):
    id = AutoField() # 自增主键
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=100)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'user'# 指定对应的数据库表名 / Specify the actual table name in database

# 对应 movie 表，存储电影基本信息（来自数据集导入）
# Maps to the 'movie' table, stores basic movie info (imported from dataset)
class Movie(BaseModel):
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200)
    genres = CharField(max_length=200, null=True)

    class Meta:
        table_name = 'movie'

# 对应 rating 表，存储用户对电影的评分
# Maps to the 'rating' table, stores user ratings for movies
class Rating(BaseModel):
    id = AutoField()
    user_id = IntegerField()
    movie_id = IntegerField()
    rating = DecimalField(max_digits=3, decimal_places=1)# 评分值，最多3位数字其中1位小数
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'rating'
        indexes = (
            # 联合唯一索引，保证一个用户对一部电影只能有一个评分，防止重复数据
            # Composite unique index: (user_id, movie_id) combination must be unique
            # one user can only have one rating per movie, no duplicate ratings
            (('user_id', 'movie_id'), True),
        )