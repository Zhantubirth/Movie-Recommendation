#The author of all functions in this module:Yaohang Zhong
from fastapi import APIRouter, HTTPException, Query
from ..models import Movie, Rating

router = APIRouter(prefix="/api/movies", tags=["电影"])


@router.get("")
#get movie list
def get_movies(
        # query arguments
        page: int = Query(1, ge=1),
        size: int = Query(50, ge=1, le=100),
        keyword: str = None,
        user_id: int = Query(None, ge=1)
):
    # Building Basic Query
    query = Movie.select()
    # 如果前端传了关键词，就加上模糊搜索条件
    #If the frontend passes keywords, add fuzzy search conditions
    if keyword:
        query = query.where(Movie.title.contains(keyword))

    # Get the total number (before sorting)
    total = query.count()

    # 如果提供了user_id，则进行已评分优先排序
    if user_id:
        # 子查询：先查出这个用户已经评过哪些电影的ID
        # Subquery: find which movie IDs this user has already rated
        user_ratings = Rating.select(Rating.movie_id).where(Rating.user_id == user_id)
        
        # 主查询：对查询结果进行排序，保证用户已评分电影的排在前面
        # Main query: Sort the query results to ensure that the movies rated by the user are ranked first
        query = (query
                 .order_by(
                     Movie.id.not_in(user_ratings).asc(),  # Rated movies first (False=0 < True=1)
                     Movie.id.asc()   # Same status sorted by ID
                 ))
    
    # Paging the results
    movies = query.paginate(page, size)

    # Build return data
    movies_data = []
    for m in movies:
        movie_dict = {
            "id": m.id, 
            "title": m.title, 
            "genres": m.genres
        }
        movies_data.append(movie_dict)

    # Return paginated data, and the frontend can display page number information
    # 返回分页数据，前端拿到后可以显示页码信息
    return {
        "movies": movies_data,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/{movie_id}")
#Get details of a single movie
def get_movie(movie_id: int):
    try:
        movie = Movie.get_by_id(movie_id)
        return {"id": movie.id, "title": movie.title, "genres": movie.genres}
    except Movie.DoesNotExist:
        raise HTTPException(status_code=404, detail="电影不存在")