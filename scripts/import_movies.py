"""
电影数据导入脚本
将 MovieLens 100k 数据集中的电影信息导入 MySQL
修正：将 genres 从数字标识改为实际类型名称
"""

import csv
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import db
from backend.app.models import Movie

# 类型编号到名称的映射（MovieLens 100k 的 19 个类型）
GENRE_MAP = {
    1: "unknown",
    2: "Action",
    3: "Adventure",
    4: "Animation",
    5: "Children's",
    6: "Comedy",
    7: "Crime",
    8: "Documentary",
    9: "Drama",
    10: "Fantasy",
    11: "Film-Noir",
    12: "Horror",
    13: "Musical",
    14: "Mystery",
    15: "Romance",
    16: "Sci-Fi",
    17: "Thriller",
    18: "War",
    19: "Western"
}


def parse_genres(genre_flags):
    """
    将类型标识（0/1列表）转换为类型名称字符串

    参数:
        genre_flags: 长度为19的列表，包含0或1

    返回:
        类型名称字符串，用 | 分隔，例如 "Animation|Comedy|Children's"
    """
    genres = []
    for i, flag in enumerate(genre_flags, start=1):
        if flag == '1' or flag == 1:
            genre_name = GENRE_MAP.get(i)
            if genre_name:
                genres.append(genre_name)
    return '|'.join(genres) if genres else 'unknown'


def import_movies(file_path):
    """
    导入电影数据到数据库

    参数:
        file_path: u.item 文件的路径
    """
    print(f"正在读取电影数据: {file_path}")

    # 连接数据库
    db.connect()

    # 统计
    total = 0
    inserted = 0
    updated = 0

    with open(file_path, 'r', encoding='latin-1') as f:
        reader = csv.reader(f, delimiter='|')

        for row in reader:
            total += 1
            movie_id = int(row[0])
            title = row[1]
            # row[5] 到 row[23] 是19个类型标识（0或1）
            genre_flags = row[5:24]
            genres_str = parse_genres(genre_flags)

            # 插入或更新
            movie, created = Movie.get_or_create(
                id=movie_id,
                defaults={
                    'title': title,
                    'genres': genres_str
                }
            )

            if not created:
                # 如果已存在，更新 genres
                movie.title = title
                movie.genres = genres_str
                movie.save()
                updated += 1
            else:
                inserted += 1

            # 每100条打印一次进度
            if total % 100 == 0:
                print(f"已处理 {total} 条...")

    print(f"\n导入完成！")
    print(f"总处理: {total} 条")
    print(f"新增: {inserted} 条")
    print(f"更新: {updated} 条")

    db.close()


# 测试函数（可选）
def test_import():
    """测试导入结果"""
    db.connect()

    # 查看前5条数据
    print("\n=== 导入结果预览 ===")
    movies = Movie.select().limit(10)
    for movie in movies:
        print(f"ID: {movie.id}, 标题: {movie.title[:40]}, 类型: {movie.genres}")

    # 统计有类型的数据量
    with_genres = Movie.select().where(Movie.genres != 'unknown').count()
    total = Movie.select().count()
    print(f"\n有类型标签的电影: {with_genres}/{total}")

    db.close()


if __name__ == "__main__":
    # 修改为你的 u.item 文件实际路径
    DATA_PATH = r"C:\Users\LIANXIANG\Desktop\ml-100k\ml-100k\u.item"

    # 检查文件是否存在
    if not os.path.exists(DATA_PATH):
        print(f"错误: 找不到文件 {DATA_PATH}")
        print("请修改 DATA_PATH 变量为你的 u.item 文件路径")
        sys.exit(1)

    import_movies(DATA_PATH)
    test_import()