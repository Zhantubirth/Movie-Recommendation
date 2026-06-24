#The author of all functions in this module:Yaohang Zhong
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 创建 FastAPI 应用实例，这是整个后端的核心入口
# Create FastAPI app instance, this is the core entry point of the backend
# 参数只是给 API 文档页面加个标题和描述，方便查看
# Parameters are just for the API docs page title and description
app = FastAPI(
    title="电影推荐系统 API",
    description="后端接口文档",
    version="1.0.0"
)

# 跨域配置，前端用 Streamlit 跑在 localhost:8501，后端跑在 localhost:8000
# 浏览器的"同源策略"会阻止不同端口之间的请求，所以后端要显式允许跨域
# CORS Configuration.Frontend (Streamlit) runs on port 8501, backend on port 8000
# Browsers "same-origin policy" blocks cross-port requests, so we must explicitly allow it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # 只允许Streamlit 默认端口
    allow_credentials=True,# 允许携带凭证
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径，访问 http://localhost:8000/ 就能看到欢迎消息，用来验证服务是否正常启动
# Root path, visit http://localhost:8000/ to see welcome message, used to verify server is running
@app.get("/")
def root():
    return {"message": "欢迎使用电影推荐系统 API"}

# 健康检查
@app.get("/health")
def health():
    return {"status": "ok"}

from backend.app.routers import user, movie, rating,recommend
# 把各个功能模块的路由注册到主应用上
# Register routers: "attach" each module's routes to the main app
app.include_router(user.router)
app.include_router(movie.router)
app.include_router(rating.router)
app.include_router(recommend.router)

# When running this file directly, start uvicorn server
if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True  # 开发模式：代码改了自动重启服务器 / Dev mode: auto-reload on code changes
    )
