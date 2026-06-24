#The authors of all functions in this module: Qiangyou Zheng,Yifu Chen
"""
Item-based 协同过滤算法
"""
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
    # 1. 如果没有评分数据，返回冷启动推荐（排除已评分电影）
    if not user_ratings:
        return cold_start_recommend(top_n, exclude_movies=set())

    # 2. 获取数据
    rating_matrix, _, _ = get_rating_matrix()
    item_similarity, movie_id_list = get_item_similarity()

    # 3. 构建电影ID到索引的映射
    movie_to_idx = {mid: idx for idx, mid in enumerate(movie_id_list)}

    # 4. 过滤出矩阵中存在的评分电影
    rated_movies = [(mid, rating) for mid, rating in user_ratings.items()
                    if mid in movie_to_idx]

    if not rated_movies:
        return cold_start_recommend(top_n, exclude_movies=set(user_ratings.keys()))

    user_mean = sum(rating for _, rating in rated_movies) / len(rated_movies)
    movie_means = {}
    for idx, movie_id in enumerate(movie_id_list):
        movie_ratings = rating_matrix.iloc[:, idx]
        movie_ratings = movie_ratings[movie_ratings > 0]
        if not movie_ratings.empty:
            movie_means[movie_id] = float(movie_ratings.mean())
#1.判断用户是否无评分，若是则调用 cold_start_recommend 冷启动
#If the user has no ratings, invoke cold_start_recommend for cold start
#2.调用 get_rating_matrix / get_item_similarity 获取缓存数据
#Fetch cached data via get_rating_matrix and get_item_similarity
#3.构建 movie_to_idx 映射，将电影 ID 转为矩阵索引
#Build movie_to_idx mapping to convert movie IDs to matrix indices
#4.过滤用户已评电影，计算 user_mean 和 movie_means 作为后续基线
#Filter rated movies, compute user_mean and movie_means as baselines for later steps

    # 5. 为每个未评分电影，累加用户对相似电影的评分偏差
    scores = {}      # 存储加权评分偏差和
    sim_sums = {}    # 存储相似度总和

    # 遍历用户已评分的每一部电影，利用物品相似度矩阵预测未评分电影的得分
    for rated_movie_id, rating in rated_movies:
        if rated_movie_id not in movie_means:
            continue

        # 获取当前已评分电影在相似度矩阵中的行索引和对应的相似度向量
        movie_idx = movie_to_idx[rated_movie_id]
        similarities = item_similarity[movie_idx]

        for other_idx, other_movie_id in enumerate(movie_id_list):
            # 跳过自身：一部电影与自身不需要计算推荐
            if other_movie_id == rated_movie_id:
                continue
            # 跳过用户已评分的电影：只预测未评分的电影
            if other_movie_id in user_ratings:
                continue

            # 获取当前已评分电影与候选电影之间的皮尔逊相似度
            sim = similarities[other_idx]
            if sim > 0:
                # 基线值：该已评分电影的全局均值；若无则用用户均值兜底（个人的平均评分习惯）
                baseline = movie_means.get(rated_movie_id, user_mean)
                # 核心公式（累加部分）：
                #   sim * (rating - baseline)
                #   = 相似度 × 用户对该电影的评分偏差（用户评分 - 电影全局均值）
                #   偏差为正说明用户打分高于平均水平，乘以相似度后加权累加到候选电影
                scores[other_movie_id] = scores.get(other_movie_id, 0) + sim * (rating - baseline)
                # 累加相似度权重，用于后续归一化
                sim_sums[other_movie_id] = sim_sums.get(other_movie_id, 0) + sim

    # 6. 计算最终预测评分：候选电影均值 + 用户对相似电影的评分偏差
    final_scores = {}
    for movie_id, weighted_deviation in scores.items():
        if sim_sums[movie_id] > 0:
            # 基线值：候选电影自身的全局均值；若无则用用户均值兜底
            baseline = movie_means.get(movie_id, user_mean)
            # 最终预测公式：
            #   score = 候选电影全局均值 + (加权偏差和 / 相似度总和)
            #   含义：在候选电影自身平均水平的基础上，
            #   根据用户对其相似电影的评分偏差进行修正
            #   偏差越大（用户偏好与这些相似电影越契合），预测分越高
            score = baseline + weighted_deviation / sim_sums[movie_id]
            final_scores[movie_id] = min(max(score, 1.0), 10.0)

    # 7. 如果没有相似电影，返回热门推荐
    if not final_scores:
        return cold_start_recommend(top_n, exclude_movies=set(user_ratings.keys()))

    # 8. 按预测评分排序
    sorted_movies = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    # 9. 如果推荐数量不足，补充热门推荐（排除已评分和已预测的电影）
    if len(sorted_movies) < top_n:
        # 获取已排除的电影集合（已评分的 + 已预测的）
        excluded_movies = set(user_ratings.keys()) | set(final_scores.keys())
        # 请求更多候选（top_n * 3），确保有足够补充
        hot_candidates = cold_start_recommend(top_n * 3, exclude_movies=excluded_movies)

        for hot_movie in hot_candidates:
            movie_id = hot_movie["movie_id"]
            if movie_id not in final_scores and movie_id not in user_ratings:
                # 给一个较低的临时分数，排在预测结果后面
                # 使用已有预测的最小值减1，如果没有预测则设为0
                temp_score = min(final_scores.values()) - 1.0 if final_scores else 0.0
                sorted_movies.append((movie_id, temp_score))
            if len(sorted_movies) >= top_n:
                break

        # 重新按分数排序（确保预测评分高的在前，补充的在后面）
        sorted_movies.sort(key=lambda x: x[1], reverse=True)

    # 10. 取最终的 Top N
    sorted_movies = sorted_movies[:top_n]

    # 11. 构建返回结果（确保没有重复）
    result = []
    seen_movie_ids = set()

    for movie_id, score in sorted_movies:
        # 去重检查
        if movie_id in seen_movie_ids:
            continue
        seen_movie_ids.add(movie_id)

        # 再次确认不是已评分的电影
        if movie_id in user_ratings:
            continue

        movie = Movie.get_or_none(Movie.id == movie_id)

        # 预测评分已经在 1-10 范围内，直接使用
        # 但确保在有效范围内
        if score > 0:
            predicted_rating = float(min(max(round(score, 1), 1.0), 10.0))
        else:
            predicted_rating = None

        result.append({
            "movie_id": movie_id,
            "title": movie.title if movie else "Unknown",
            "predicted_rating": predicted_rating,
            "reason": "Similar to movies you have rated"
        })

    return result
#1.若 A 计算结果为空，再次调用 cold_start_recommend 兜底
#If Developer A's final_scores is empty, fall back to cold_start_recommend
#2.按预测评分降序排序
#Sort by predicted rating in descending order
#3.推荐数量不足时，用热门电影填充并赋予较低临时分数
#Pad with popular movies and assign a lower temporary score when results are insufficient
#4.截取 Top N 推荐
#Take the top N recommendations
#5.查询 Movie 表获取标题，去重后组装 JSON（movie_id, title, predicted_rating, reason）
#Query the Movie table for titles, deduplicate, and assemble JSON output