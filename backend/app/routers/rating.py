#The author of all functions in this module:Yaohang Zhong
from fastapi import APIRouter, HTTPException
from ..models import Rating
from pydantic import BaseModel

router = APIRouter(prefix="/api/ratings", tags=["Ratings"])

# the structure of request body,using Pydantic BaseModel
class RatingCreate(BaseModel):
    user_id: int
    movie_id: int
    rating: float

class RatingDelete(BaseModel):
    user_id: int
    movie_id: int

@router.post("")
def create_rating(rating_data: RatingCreate):
    try:
        # Validate rating range
        if rating_data.rating < 1.0 or rating_data.rating > 10.0:
            raise HTTPException(status_code=400, detail="Rating must be between 1.0 and 10.0")

        # Peewee 的get_or_create 方法，一步完成"先查有没有 → 有就返回 / 没有就新建"
        # 返回值是一个元组：(对象, 是否新建)
        #Peevee's get_or_create method, which completes the process in one step:
        # "Check if there exist any record first,Create if there is no, the return value is a tuple
        rating, created = Rating.get_or_create(
            user_id=rating_data.user_id,
            movie_id=rating_data.movie_id,
            defaults={"rating": rating_data.rating}#The rating field only takes effect when created, and the rating value is written in.
        )
        # 如果没新建（说明之前已经评过分），就更新评分
        # If not created (user already rated this movie), update the rating
        if not created:
            rating.rating = rating_data.rating
            rating.save() # save changes back to database
        
        return {
            "code": 200,
            "message": "Rating created" if created else "Rating updated",
            "rating": float(rating.rating)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save rating: {str(e)}")

@router.get("/{user_id}")
def get_user_ratings(user_id: int):
    try:
        ratings = Rating.select().where(Rating.user_id == user_id)
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "movie_id": r.movie_id,
                "rating": float(r.rating),#Type conversion is required for JSON serialization
                "created_at": r.created_at.isoformat()
            }
            for r in ratings
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ratings: {str(e)}")

@router.delete("/{user_id}/{movie_id}")
def delete_rating(user_id: int, movie_id: int):
    try:
        deleted = Rating.delete().where(
            (Rating.user_id == user_id) & 
            (Rating.movie_id == movie_id)
        ).execute()# execute() method returns the number of affected rows
        
        if deleted > 0:
            return {"code": 200, "message": "Rating removed"}
        else:
            return {"code": 404, "message": "Rating not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete rating: {str(e)}")
