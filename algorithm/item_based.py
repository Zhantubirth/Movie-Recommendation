"""
Item-based 协同过滤算法
"""
import numpy as np
from .utils import get_rating_matrix, get_item_similarity, cold_start_recommend
from backend.app.models import Movie


def recommend(user_ratings: dict, top_n: int = 10) -> list:
    """
    基于物品的协同过滤推荐

    参数:
        user_ratings: {movie_id: rating, ...} 用户已有的评分
        top_n: 推荐数量

    返回:
        list: [{"movie_id": 1, "title": "电影名", "predicted_rating": 4.8, "reason": "..."}, ...]
    """
    # 1. 如果没有评分数据，返回冷启动推荐
    if not user_ratings:
        return cold_start_recommend(top_n)

    # 2. 获取数据
    rating_matrix, user_ids, movie_ids = get_rating_matrix()
    item_similarity, movie_id_list = get_item_similarity()

    # 3. 构建电影ID到索引的映射
    movie_to_idx = {mid: idx for idx, mid in enumerate(movie_id_list)}

    # 4. 过滤出矩阵中存在的评分电影
    rated_movies = [(mid, rating) for mid, rating in user_ratings.items()
                    if mid in movie_to_idx]

    if not rated_movies:
        return cold_start_recommend(top_n)

    # 5. 为每个已评分电影，找相似的电影
    scores = {}

    for rated_movie_id, rating in rated_movies:
        movie_idx = movie_to_idx[rated_movie_id]
        similarities = item_similarity[movie_idx]

        for other_idx, other_movie_id in enumerate(movie_id_list):
            if other_movie_id == rated_movie_id:
                continue
            if other_movie_id in user_ratings:
                continue

            sim = similarities[other_idx]
            if sim > 0:
                score = rating * sim
                if other_movie_id not in scores:
                    scores[other_movie_id] = 0
                scores[other_movie_id] += score

    # 6. 如果没有相似电影，返回热门推荐
    if not scores:
        return cold_start_recommend(top_n)

    # 7. 按总分排序
    sorted_movies = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # 8. 构建返回结果
    result = []
    for movie_id, score in sorted_movies:
        movie = Movie.get_or_none(Movie.id == movie_id)
        # 归一化到 1-10 范围（假设最大可能分数是 10 * 10 = 100）
        normalized_score = min(score / 10, 10.0)
        result.append({
            "movie_id": movie_id,
            "title": movie.title if movie else "未知",
            "predicted_rating": round(normalized_score, 1),
            "reason": "与您评分过的电影相似"
        })

    return result