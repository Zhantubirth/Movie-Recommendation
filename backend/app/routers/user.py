#The author of all functions in this module:Yaohang Zhong
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..models import User

# 创建路由器，prefix 表示这组接口统一以 /api/user 开头
# tags 是给自动生成的 API 文档（/docs）分组用的
# Create router, prefix means all endpoints start with /api/user
# tags is for grouping in auto-generated API docs (/docs)
router = APIRouter(prefix="/api/user", tags=["用户"])


# the structure of request body,using Pydantic BaseModel
# If a field violates rules (e.g. empty username), FastAPI auto-returns 422 error
class UserCreate(BaseModel):
    # Field(...) means required
    username: str = Field(..., min_length=1, max_length=50, description="用户名，不能为空")
    password: str = Field(..., min_length=1, max_length=100, description="密码，不能为空")


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, description="用户名，不能为空")
    password: str = Field(..., min_length=1, description="密码，不能为空")


# 注册
@router.post("/register")
def register(user: UserCreate):
    # user: UserCreate 这一步，FastAPI 会自动把请求 JSON 解析成 UserCreate 对象并校验
    # FastAPI auto-parses request JSON into UserCreate object and validates it

    # Execute the methods that in Peewee to check if username already existed in database
    if User.select().where(User.username == user.username).exists():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # create new user
    new_user = User.create(username=user.username, password=user.password)
    return {"code": 200, "user_id": new_user.id, "message": "注册成功"}


# 登录
@router.post("/login")
def login(user: UserLogin):
    try:
        # Peewee's get() fetches the first matching record
        db_user = User.get(User.username == user.username, User.password == user.password)
        return {"code": 200, "user_id": db_user.id, "username": db_user.username}
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="用户名或密码错误")