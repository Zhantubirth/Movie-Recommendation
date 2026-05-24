"""
User-based 协同过滤算法
"""
import numpy as np
from .utils import get_rating_matrix, get_user_similarity, cold_start_recommend
from backend.app.models import Movie


def recommend(user_id: int, top_n: int = 10) -> list:
    """
    基于用户的协同过滤推荐

    参数:
        user_id: 用户ID
        top_n: 推荐数量

    返回:
        list: [{"movie_id": 1, "title": "电影名", "predicted_rating": 4.8, "reason": "..."}, ...]
    """
    # 1. 获取数据
    rating_matrix, user_ids, movie_ids = get_rating_matrix()
    user_similarity, _ = get_user_similarity()

    # 2. 检查用户是否存在
    if user_id not in user_ids:
        return cold_start_recommend(top_n)

    # 3. 获取用户索引
    user_idx = user_ids.index(user_id)

    # 4. 获取该用户与其他所有用户的相似度
    similarities = user_similarity[user_idx]

    # 5. 找到最相似的 K 个用户（K=20）
    K = min(20, len(user_ids) - 1)
    if K <= 0:
        return cold_start_recommend(top_n)

    similar_users_idx = np.argsort(similarities)[::-1][1:K + 1]

    # 6. 获取当前用户已评分的电影
    user_rated_mask = rating_matrix.iloc[user_idx] > 0
    rated_movies = set(rating_matrix.columns[user_rated_mask].tolist())

    # 7. 计算每个未评分电影的预测评分
    predictions = {}

    for movie_idx, movie_id in enumerate(movie_ids):
        if movie_id in rated_movies:
            continue

        total_sim = 0
        weighted_rating = 0

        for sim_user_idx in similar_users_idx:
            sim = similarities[sim_user_idx]
            rating = rating_matrix.iloc[sim_user_idx, movie_idx]

            if rating > 0:
                total_sim += sim
                weighted_rating += sim * rating

        if total_sim > 0:
            predictions[movie_id] = weighted_rating / total_sim

    # 8. 如果没有预测结果，返回热门推荐
    if not predictions:
        return cold_start_recommend(top_n)

    # 9. 按预测评分排序，取 Top N
    sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # 10. 构建返回结果
    result = []
    for movie_id, pred_rating in sorted_predictions:
        movie = Movie.get_or_none(Movie.id == movie_id)
        result.append({
            "movie_id": movie_id,
            "title": movie.title if movie else "未知",
            "predicted_rating": round(min(pred_rating, 10.0), 1),  # 限制最大10分
            "reason": "其他品味相似的用户也喜欢这部电影"
        })

    return result