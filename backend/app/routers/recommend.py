#The author of all functions in this module:Yaohang Zhong
from fastapi import APIRouter, Query
from algorithm.utils import refresh_data
from backend.app.models import Rating
from algorithm.item_based import recommend as item_recommend

router = APIRouter(prefix="/api/recommend", tags=["推荐"])


@router.get("")
#Get personalized recommendations
def get_recommendations(
        user_id: int,
        top_n: int = Query(10, ge=1, le=50)#Recommended Quantity
):
    # 第一步：从数据库查出该用户所有的评分记录
    # Step 1: Fetch all rating records for this user from database
    ratings = Rating.select().where(Rating.user_id == user_id)
    # 第二步：把评分记录转成字典
    # Step 2: Convert rating records to dictionary
    user_ratings = {r.movie_id: float(r.rating) for r in ratings}

    # 第三步：使用基于物品的协同过滤算法获取推荐
    # Step 3: Use item-based collaborative filtering algorithm to get recommendations
    recommendations = item_recommend(user_ratings, top_n)

    return {"code": 200, "recommendations": recommendations}

@router.post("/refresh")
# 什么时候用？比如导入了新的评分数据后，需要让算法重新计算相似度矩阵
# When to use:After importing new rating data, need to recalculate similarity matrix
def refresh_cache():
    refresh_data()
    return {"code": 200, "message": "缓存已刷新"}
