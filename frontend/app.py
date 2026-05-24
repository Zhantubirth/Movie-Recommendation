
import streamlit as st
import requests
import time

# ==================== 配置 ====================
API_BASE_URL = "http://localhost:8000/api"

# 页面配置
st.set_page_config(
    page_title="电影推荐系统",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 初始化 session 状态 ====================
# 这些状态在页面刷新后会保留
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "algorithm" not in st.session_state:
    st.session_state.algorithm = "user"
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "user_ratings" not in st.session_state:
    st.session_state.user_ratings = {}  # {movie_id: rating}
if "rating_pending" not in st.session_state:
    st.session_state.rating_pending = {}  # {movie_id: pending_rating}


# ==================== 辅助函数 ====================
def call_api(method: str, endpoint: str, data=None, params=None):
    """统一的 API 调用函数"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return None, f"不支持的请求方法: {method}"

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"请求失败: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "无法连接到后端服务，请确认后端已启动（http://localhost:8000）"
    except Exception as e:
        return None, f"请求异常: {str(e)}"


def load_movies(page=1, size=20, keyword=""):
    """加载电影列表"""
    params = {"page": page, "size": size}
    if keyword:
        params["keyword"] = keyword
    return call_api("GET", "/movies", params=params)


def submit_rating(user_id, movie_id, rating):
    """提交评分"""
    data = {"user_id": user_id, "movie_id": movie_id, "rating": rating}
    return call_api("POST", "/ratings", data=data)


def get_user_ratings(user_id):
    """获取用户的历史评分"""
    return call_api("GET", f"/ratings/{user_id}")


def get_recommendations(user_id, algorithm, top_n=10):
    """获取推荐"""
    params = {"user_id": user_id, "algorithm": algorithm, "top_n": top_n}
    return call_api("GET", "/recommend", params=params)


def refresh_cache():
    """刷新算法缓存"""
    return call_api("POST", "/recommend/refresh")


# ==================== 侧边栏：用户登录/注册 ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/movie-projector.png", width=80)
    st.title("🎬 电影推荐系统")
    st.markdown("---")

    if not st.session_state.logged_in:
        st.subheader("🔐 用户中心")
        tab1, tab2 = st.tabs(["登录", "注册"])

        with tab1:
            login_username = st.text_input("用户名", key="login_user", placeholder="请输入用户名")
            login_password = st.text_input("密码", type="password", key="login_pwd", placeholder="请输入密码")

            if st.button("登录", type="primary", use_container_width=True):
                if login_username and login_password:
                    result, err = call_api("POST", "/user/login",
                                           data={"username": login_username, "password": login_password})
                    if result and result.get("code") == 200:
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.recommendations = []
                        st.session_state.rating_pending = {}
                        
                        ratings_result, _ = get_user_ratings(result["user_id"])
                        if ratings_result:
                            st.session_state.user_ratings = {
                                r["movie_id"]: r["rating"] for r in ratings_result
                            }
                        else:
                            st.session_state.user_ratings = {}
                        
                        st.rerun()
                    else:
                        st.error(err or "用户名或密码错误")
                else:
                    st.warning("请输入用户名和密码")

        with tab2:
            reg_username = st.text_input("用户名", key="reg_user", placeholder="请输入用户名")
            reg_password = st.text_input("密码", type="password", key="reg_pwd", placeholder="请输入密码")
            reg_confirm = st.text_input("确认密码", type="password", key="reg_cfm", placeholder="请再次输入密码")

            if st.button("注册", type="primary", use_container_width=True):
                if not reg_username or not reg_password:
                    st.warning("请填写完整信息")
                elif reg_password != reg_confirm:
                    st.warning("两次输入的密码不一致")
                else:
                    result, err = call_api("POST", "/user/register",
                                           data={"username": reg_username, "password": reg_password})
                    if result and result.get("code") == 200:
                        st.success("注册成功！请登录")
                        st.rerun()
                    else:
                        st.error(err or "注册失败，用户名可能已存在")

    else:
        st.success(f"👤 当前用户：**{st.session_state.username}**")
        st.info(f"🆔 用户ID：`{st.session_state.user_id}`")

        st.markdown("---")

        # 算法选择
        st.subheader("⚙️ 推荐设置")
        algorithm_options = {
            "user": "👥 基于用户（找相似用户）",
            "item": "🎬 基于物品（找相似电影）"
        }
        selected_algo = st.radio(
            "选择推荐算法",
            options=["user", "item"],
            format_func=lambda x: algorithm_options[x],
            horizontal=True
        )
        st.session_state.algorithm = selected_algo

        st.markdown("---")

        if st.button("🚪 退出登录", use_container_width=True):
            # 清空所有状态
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ==================== 主区域 ====================
if not st.session_state.logged_in:
    # 未登录时显示欢迎页
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1>🎬 电影推荐系统</h1>
            <p style="font-size: 18px; color: gray;">
                基于协同过滤算法的个性化电影推荐<br>
                登录后即可开始你的电影之旅
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 **使用说明**\n\n1. 左侧登录或注册\n2. 给喜欢的电影评分\n3. 选择算法获取推荐")

else:
    # 已登录：主界面
    st.header(f"🎬 欢迎回来，{st.session_state.username}！")

    # 两列布局：左侧电影列表，右侧推荐结果
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("📋 电影列表")

        # 搜索框和分页放在同一行
        search_col, page_col = st.columns([3, 1])
        with search_col:
            search_keyword = st.text_input("🔍 搜索电影", placeholder="输入电影名称...", key="search_input", label_visibility="collapsed")
        with page_col:
            st.write("")  # 占位对齐
            page_control = st.columns([1, 2, 1])
            with page_control[0]:
                if st.button("◀", key="prev_page", use_container_width=True):
                    if st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                        st.rerun()
            with page_control[1]:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'>第 {st.session_state.current_page} 页</div>", unsafe_allow_html=True)
            with page_control[2]:
                if st.button("▶", key="next_page", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()

        # 加载电影数据
        with st.spinner("加载电影列表中..."):
            result, err = load_movies(
                page=st.session_state.current_page,
                size=20,
                keyword=search_keyword if search_keyword else ""
            )

        if err:
            st.error(err)
        elif result and result.get("movies"):
            movies = result["movies"]
            total = result.get("total", 0)
            
            movies_with_rating_status = []
            for movie in movies:
                movie_id = movie['id']
                has_rated = movie_id in st.session_state.user_ratings
                movies_with_rating_status.append((movie, has_rated))
            
            movies_with_rating_status.sort(key=lambda x: not x[1])
            
            st.caption(f"共 {total} 部电影，当前显示 {len(movies)} 部")

            for movie, has_rated in movies_with_rating_status:
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([4, 1, 1])
                    with col_a:
                        st.write(f"**{movie['title']}**")
                        genres = movie.get('genres', '未知类型')[:50]
                        st.caption(genres)
                        
                        movie_id = movie['id']
                        if movie_id in st.session_state.user_ratings:
                            current_rating = st.session_state.user_ratings[movie_id]
                            st.markdown(f"<span style='color: orange;'>⭐ 已评分: {current_rating}/10</span>", unsafe_allow_html=True)
                    
                    with col_b:
                        existing_rating = st.session_state.user_ratings.get(movie['id'], 0)
                        pending_rating = st.session_state.rating_pending.get(movie['id'], existing_rating)
                        
                        selected_rating = st.selectbox(
                            "评分",
                            options=[0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                            key=f"rating_{movie['id']}",
                            label_visibility="collapsed",
                            index=0 if pending_rating == 0 else int(pending_rating)
                        )
                        
                        if selected_rating > 0 and selected_rating != pending_rating:
                            st.session_state.rating_pending[movie['id']] = selected_rating
                    
                    with col_c:
                        pending = st.session_state.rating_pending.get(movie['id'], 0)
                        if pending > 0:
                            if st.button("提交", key=f"submit_{movie['id']}", use_container_width=True, type="primary"):
                                result, err = submit_rating(st.session_state.user_id, movie['id'], pending)
                                if result:
                                    st.session_state.user_ratings[movie['id']] = pending
                                    del st.session_state.rating_pending[movie['id']]
                                    refresh_cache()
                                    st.toast(f"✅ 已为《{movie['title']}》评分 {pending}")
                                    st.rerun()
                                else:
                                    st.error(err or "评分失败")
                                    if movie['id'] in st.session_state.rating_pending:
                                        del st.session_state.rating_pending[movie['id']]
                        elif existing_rating > 0:
                            st.markdown("<div style='text-align: center; padding-top: 8px;'>✓</div>", unsafe_allow_html=True)

        else:
            st.info("暂无电影数据，请先导入数据集")

    with right_col:
        st.subheader("🎯 为你推荐")

        # 推荐数量选择
        top_n = st.selectbox("推荐数量", options=[5, 10, 15, 20], index=1, label_visibility="collapsed")

        # 获取推荐按钮
        if st.button("🔍 获取推荐", type="primary", use_container_width=True):
            with st.spinner("正在生成推荐..."):
                result, err = get_recommendations(
                    st.session_state.user_id,
                    st.session_state.algorithm,
                    top_n
                )
                if result and result.get("code") == 200:
                    st.session_state.recommendations = result.get("recommendations", [])
                    if not st.session_state.recommendations:
                        st.info("暂无推荐结果，请先给一些电影评分")
                else:
                    st.error(err or "获取推荐失败")
                    st.session_state.recommendations = []

        # 显示推荐结果
        if st.session_state.recommendations:
            st.markdown("---")
            for idx, rec in enumerate(st.session_state.recommendations[:top_n], 1):
                with st.container(border=True):
                    st.write(f"**{idx}. {rec.get('title', '未知电影')}**")
                    
                    movie_id = rec.get('id') or rec.get('movie_id')
                    if movie_id and movie_id in st.session_state.user_ratings:
                        user_rating = st.session_state.user_ratings[movie_id]
                        st.write(f"⭐ 您的评分：**{user_rating}/10**")
                    
                    if rec.get('predicted_rating'):
                        st.write(f"🎯 预测评分：{rec['predicted_rating']} / 10")
                    
                    reason = rec.get('reason', '')
                    if not reason or '暂无' in reason or '默认' in reason:
                        if movie_id and movie_id in st.session_state.user_ratings:
                            reason = f"基于您的观影历史推荐"
                        else:
                            reason = f"根据您的偏好推荐"
                    st.caption(f" {reason}")
        else:
            st.info("点击「获取推荐」查看个性化推荐")


# ==================== 页脚 ====================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "电影推荐系统 | 基于协同过滤算法 | 数据来源：MovieLens"
    "</div>",
    unsafe_allow_html=True
)