"""
算法工具函数：加载数据、计算相似度等
"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.models import Rating, Movie
from peewee import fn

# 全局缓存（启动后只加载一次）
_rating_matrix = None
_user_similarity = None
_item_similarity = None
_user_ids = None
_movie_ids = None


def load_data():
    """从数据库加载评分数据，构建评分矩阵"""
    global _rating_matrix, _user_similarity, _item_similarity, _user_ids, _movie_ids

    print("正在加载评分数据...")

    # 1. 获取所有用户ID和电影ID
    users = Rating.select(Rating.user_id).distinct()
    movies = Rating.select(Rating.movie_id).distinct()

    _user_ids = sorted(list(set([u.user_id for u in users])))
    _movie_ids = sorted(list(set([m.movie_id for m in movies])))

    # 2. 构建用户-电影评分矩阵
    data = []
    for user_id in _user_ids:
        row = {}
        ratings = Rating.select().where(Rating.user_id == user_id)
        for r in ratings:
            row[r.movie_id] = float(r.rating)
        data.append(row)

    _rating_matrix = pd.DataFrame(data, index=_user_ids, columns=_movie_ids).fillna(0)

    # 3. 计算用户相似度矩阵
    print("正在计算用户相似度矩阵...")
    matrix_values = _rating_matrix.values
    _user_similarity = cosine_similarity(matrix_values)

    # 4. 计算物品相似度矩阵（转置）
    print("正在计算物品相似度矩阵...")
    item_matrix = _rating_matrix.T
    item_values = item_matrix.values
    _item_similarity = cosine_similarity(item_values)

    print(f"数据加载完成: {len(_user_ids)} 个用户, {len(_movie_ids)} 部电影")


def get_rating_matrix():
    """获取评分矩阵"""
    if _rating_matrix is None:
        load_data()
    return _rating_matrix, _user_ids, _movie_ids


def get_user_similarity():
    """获取用户相似度矩阵"""
    if _user_similarity is None:
        load_data()
    return _user_similarity, _user_ids


def get_item_similarity():
    """获取物品相似度矩阵"""
    if _item_similarity is None:
        load_data()
    return _item_similarity, _movie_ids


def cold_start_recommend(top_n: int = 10) -> list:
    """冷启动推荐：返回评分次数最多的热门电影"""
    query = (Rating
             .select(Rating.movie_id, fn.COUNT(Rating.movie_id).alias('count'))
             .group_by(Rating.movie_id)
             .order_by(fn.COUNT(Rating.movie_id).desc())
             .limit(top_n))

    result = []
    for row in query:
        movie = Movie.get_or_none(Movie.id == row.movie_id)
        result.append({
            "movie_id": row.movie_id,
            "title": movie.title if movie else "未知",
            "predicted_rating": None,
            "reason": "热门电影推荐（暂无您的评分数据）"
        })

    # 如果评分数据不足（比如新项目还没有评分），返回一些默认电影
    if len(result) < top_n:
        default_movies = Movie.select().limit(top_n)
        for movie in default_movies:
            if not any(r["movie_id"] == movie.id for r in result):
                result.append({
                    "movie_id": movie.id,
                    "title": movie.title,
                    "predicted_rating": None,
                    "reason": "默认推荐"
                })

    return result[:top_n]

# 在 algorithm/utils.py 末尾添加

def refresh_data():
    """强制刷新数据缓存"""
    global _rating_matrix, _user_similarity, _item_similarity, _user_ids, _movie_ids
    _rating_matrix = None
    _user_similarity = None
    _item_similarity = None
    _user_ids = None
    _movie_ids = None
    load_data()
    print("数据缓存已刷新")