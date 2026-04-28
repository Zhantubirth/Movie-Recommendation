from fastapi import APIRouter, HTTPException
from pydantic import BaseModel,Field
from ..models import Rating, Movie

router = APIRouter(prefix="/api/ratings", tags=["评分"])


class RatingCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    movie_id: int = Field(..., gt=0)
    rating: float = Field(..., ge=1.0, le=10.0, description="评分范围 1.0 ~ 10.0")


@router.post("")
def submit_rating(rating: RatingCreate):
    # Pydantic 已经校验了范围，这行可以删除或保留作为双重保障
    if rating.rating < 1.0 or rating.rating > 10.0:
        raise HTTPException(status_code=400, detail="评分必须在 1.0-10.0 之间")

    # 验证电影是否存在
    try:
        Movie.get_by_id(rating.movie_id)
    except Movie.DoesNotExist:
        raise HTTPException(status_code=404, detail="电影不存在")

    # 插入或更新评分 (ON CONFLICT UPDATE)
    # Peewee 的 replace 或 get_or_create 实现 upsert
    r, created = Rating.get_or_create(
        user_id=rating.user_id,
        movie_id=rating.movie_id,
        defaults={'rating': rating.rating}
    )
    if not created:
        r.rating = rating.rating
        r.save()

    return {"code": 200, "message": "评分成功"}


@router.get("/{user_id}")
def get_user_ratings(user_id: int):
    ratings = Rating.select().where(Rating.user_id == user_id).order_by(Rating.created_at.desc())
    result = []
    for r in ratings:
        movie = Movie.get_or_none(Movie.id == r.movie_id)
        result.append({
            "movie_id": r.movie_id,
            "title": movie.title if movie else "未知",
            "rating": float(r.rating),
            "created_at": r.created_at.isoformat()
        })
    return result