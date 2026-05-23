"""
电影推荐系统 - 前端界面 (Streamlit)
适配后端 FastAPI 接口：
- 用户: /api/user/register, /api/user/login
- 电影: /api/movies
- 评分: /api/ratings (POST), /api/ratings/{user_id} (GET)
推荐接口尚未提供，暂时使用演示数据或提示开发中
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ----------------------------- 配置 -----------------------------
API_BASE_URL = "http://localhost:8000"  # 后端 FastAPI 服务地址

# 接口端点（完全匹配后端路由）
ENDPOINTS = {
    "register": f"{API_BASE_URL}/api/user/register",
    "login": f"{API_BASE_URL}/api/user/login",
    "movies": f"{API_BASE_URL}/api/movies",
    "ratings": f"{API_BASE_URL}/api/ratings",  # POST 评分 & GET 用户评分历史
}

# 演示模式开关（当后端未就绪时使用）
DEMO_MODE = False  # 改为 False 使用真实后端


# 辅助函数：发送 HTTP 请求
def api_call(method, url, data=None, params=None):
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=10)
        else:
            return None
        # 后端在错误时返回非200状态码，并包含 detail 字段
        if resp.status_code == 200:
            return resp.json()
        else:
            error_detail = resp.json().get("detail", "未知错误")
            st.error(f"请求失败 ({resp.status_code}): {error_detail}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"无法连接到后端服务，请确保后端已启动在 {API_BASE_URL}")
        return None
    except Exception as e:
        st.error(f"网络错误: {str(e)}")
        return None


# 演示模式数据（与后端字段保持一致）
def demo_register(username, password):
    return {"code": 200, "user_id": 1, "message": "注册成功"}


def demo_login(username, password):
    if username and password:
        return {"code": 200, "user_id": 1, "username": username}
    return None


def demo_get_movies(page=1, size=50):
    return {
        "movies": [
            {"id": 1, "title": "肖申克的救赎", "genres": "剧情"},
            {"id": 2, "title": "盗梦空间", "genres": "科幻"},
            {"id": 3, "title": "寻梦环游记", "genres": "动画"},
            {"id": 4, "title": "教父", "genres": "犯罪"},
            {"id": 5, "title": "星际穿越", "genres": "科幻"},
        ],
        "total": 5,
        "page": 1,
        "size": 5
    }


def demo_submit_rating(user_id, movie_id, rating):
    return {"code": 200, "message": "评分成功"}


def demo_get_user_ratings(user_id):
    return [
        {"movie_id": 1, "title": "肖申克的救赎", "rating": 8.0, "created_at": "2025-01-01T10:00:00"},
        {"movie_id": 2, "title": "盗梦空间", "rating": 9.0, "created_at": "2025-01-02T11:00:00"},
    ]


# ---------- 真实 API 调用函数 ----------
def register_user(username, password):
    if DEMO_MODE:
        return demo_register(username, password)
    return api_call("POST", ENDPOINTS["register"], data={"username": username, "password": password})


def login_user(username, password):
    if DEMO_MODE:
        return demo_login(username, password)
    return api_call("POST", ENDPOINTS["login"], data={"username": username, "password": password})


def fetch_movies(page=1, size=50, keyword=None):
    if DEMO_MODE:
        return demo_get_movies(page, size)
    params = {"page": page, "size": size}
    if keyword:
        params["keyword"] = keyword
    return api_call("GET", ENDPOINTS["movies"], params=params)


def submit_rating(user_id, movie_id, rating_star):  # rating_star: 1~5
    # 将前端 1-5 星转换为后端 1-10 分（乘以2）
    backend_rating = rating_star * 2.0
    if DEMO_MODE:
        return demo_submit_rating(user_id, movie_id, backend_rating)
    data = {"user_id": user_id, "movie_id": movie_id, "rating": backend_rating}
    return api_call("POST", ENDPOINTS["ratings"], data=data)


def fetch_user_ratings(user_id):
    if DEMO_MODE:
        return demo_get_user_ratings(user_id)
    url = f"{ENDPOINTS['ratings']}/{user_id}"
    return api_call("GET", url)  # 返回列表，可能为None


# ---------- 页面配置 ----------
st.set_page_config(page_title="电影推荐系统", page_icon="🎬", layout="wide")
st.title("🎬 智能电影推荐系统")
st.markdown("基于协同过滤算法的个性化电影推荐")

# 初始化 session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.user_ratings = {}  # {movie_id: rating_backend} 用于展示
    st.session_state.algo = "user"  # 推荐算法类型，后端未实现，预留

# ----------------------------- 侧边栏登录/注册 -----------------------------
with st.sidebar:
    st.header("👤 用户中心")
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["登录", "注册"])
        with tab1:
            login_username = st.text_input("用户名", key="login_username")
            login_password = st.text_input("密码", type="password", key="login_password")
            if st.button("登录", use_container_width=True):
                result = login_user(login_username, login_password)
                if result and result.get("code") == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_id = result["user_id"]
                    st.session_state.username = result["username"]
                    # 登录后获取用户历史评分
                    ratings_data = fetch_user_ratings(st.session_state.user_id)
                    if ratings_data and isinstance(ratings_data, list):
                        st.session_state.user_ratings = {r["movie_id"]: r["rating"] for r in ratings_data}
                    st.success(f"欢迎回来，{st.session_state.username}！")
                    st.rerun()
                else:
                    st.error("登录失败，请检查用户名和密码")
        with tab2:
            reg_username = st.text_input("用户名", key="reg_username")
            reg_password = st.text_input("密码", type="password", key="reg_password")
            if st.button("注册", use_container_width=True):
                result = register_user(reg_username, reg_password)
                if result and result.get("code") == 200:
                    st.success("注册成功，请登录")
                else:
                    st.error("注册失败，" + result.get("message", "用户名可能已存在"))
    else:
        st.success(f"已登录：{st.session_state.username}")
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()
        st.subheader("⚙️ 推荐设置")
        st.session_state.algo = st.radio(
            "选择推荐算法",
            options=["user", "item"],
            format_func=lambda
                x: "基于用户的协同过滤 (User-based)" if x == "user" else "基于物品的协同过滤 (Item-based)",
            horizontal=True,
            disabled=True  # 由于后端未实现推荐接口，暂时禁用
        )
        st.caption("⚠️ 推荐功能开发中，请等待后端提供接口")

# ----------------------------- 主界面 -----------------------------
if not st.session_state.logged_in:
    st.info("👈 请在左侧登录或注册，使用个性化推荐功能")
    st.stop()

# 1. 获取电影列表（前50部，简单分页可后续扩展）
movies_data = fetch_movies(page=1, size=50)
if not movies_data or "movies" not in movies_data:
    st.warning("无法获取电影列表，请检查后端服务")
    st.stop()

movies = movies_data["movies"]

# 2. 展示电影评分区域
st.subheader("📝 给电影评分")
st.markdown("点击星星评分（1-5星），提交后系统会学习您的偏好")

# 分三列显示
cols = st.columns(3)
for idx, movie in enumerate(movies):
    with cols[idx % 3]:
        with st.container(border=True):
            st.markdown(f"**{movie['title']}**")
            st.caption(f"类型：{movie.get('genres', '未知')}")

            # 获取用户对该电影的已有评分（后端存储为1-10，转换为1-5展示）
            current_backend_rating = st.session_state.user_ratings.get(movie['id'], 0)
            if current_backend_rating > 0:
                current_star = current_backend_rating / 2.0  # 转换为星
            else:
                current_star = 0

            # 滑块 (1-5星，整数步长)
            new_star = st.slider(
                "我的评分",
                min_value=0.0,
                max_value=5.0,
                value=float(current_star),
                step=1.0,
                key=f"rating_{movie['id']}",
                label_visibility="collapsed",
                format="%.0f 星"
            )
            if new_star != current_star:
                # 提交评分
                if new_star > 0:
                    with st.spinner("提交中..."):
                        result = submit_rating(st.session_state.user_id, movie['id'], new_star)
                    if result and result.get("code") == 200:
                        # 更新本地缓存
                        st.session_state.user_ratings[movie['id']] = new_star * 2.0
                        st.toast(f"已为《{movie['title']}》评分 {int(new_star)} 星", icon="✅")
                        st.rerun()
                    else:
                        st.toast(f"评分失败", icon="❌")
                else:
                    # 如果用户选择0星，表示删除评分？后端未提供删除接口，暂忽略
                    pass

# 3. 历史评分展示
with st.expander("📜 我的评分历史"):
    if st.session_state.user_ratings:
        history = []
        for movie_id, backend_rating in st.session_state.user_ratings.items():
            movie_title = next((m["title"] for m in movies if m["id"] == movie_id), "未知电影")
            star_rating = backend_rating / 2.0
            history.append({"电影": movie_title, "我的评分（星）": f"{star_rating:.0f}⭐"})
        if history:
            st.dataframe(pd.DataFrame(history), use_container_width=True)
        else:
            st.write("暂无评分记录")
    else:
        st.write("暂无评分记录")

# 4. 推荐结果区域（后端尚未实现，暂用提示）
st.divider()
st.subheader("🎯 个性化推荐")
st.info("推荐功能正在开发中，请等待后端提供 `/api/recommendations` 接口。届时前端将自动显示推荐结果。")

# #如果需要临时演示，可以取消注释以下模拟推荐代码
# st.subheader("🎯 个性化推荐（演示模式）")
# recommended_movies = [
#     {"title": "盗梦空间", "reason": "与您喜欢的《星际穿越》风格相似", "score": 4.8},
#     {"title": "楚门的世界", "reason": "其他喜欢《肖申克的救赎》的用户也喜欢", "score": 4.6},
# ]
# cols_rec = st.columns(2)
# for i, rec in enumerate(recommended_movies):
#     with cols_rec[i % 2]:
#         with st.container(border=True):
#             st.markdown(f"### {rec['title']}")
#             st.markdown(f"**推荐理由**：{rec['reason']}")
#             st.markdown(f"**预测评分**：⭐ {rec['score']}")