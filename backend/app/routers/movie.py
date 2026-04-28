from fastapi import APIRouter, HTTPException, Query
from ..models import Movie

router = APIRouter(prefix="/api/movies", tags=["电影"])


@router.get("")
def get_movies(
        page: int = Query(1, ge=1),
        size: int = Query(50, ge=1, le=100),
        keyword: str = None
):
    # 构建查询
    query = Movie.select()
    if keyword:
        query = query.where(Movie.title.contains(keyword))

    # 分页
    total = query.count()
    movies = query.paginate(page, size)

    return {
        "movies": [{"id": m.id, "title": m.title, "genres": m.genres} for m in movies],
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/{movie_id}")
def get_movie(movie_id: int):
    try:
        movie = Movie.get_by_id(movie_id)
        return {"id": movie.id, "title": movie.title, "genres": movie.genres}
    except Movie.DoesNotExist:
        raise HTTPException(status_code=404, detail="电影不存在")