#The author of all functions in this module:Yaohang Zhong
"""
电影数据导入脚本
将 MovieLens 100k 数据集中的电影信息导入 MySQL

Movie data import script
Import movie info from MovieLens 100k dataset into MySQL
"""

import csv
import sys
import os

# 把项目根目录加到 Python 搜索路径中
# 因为这个脚本在 scripts/ 子目录下，Python 默认找不到 backend 模块
# os.path.abspath(__file__) → 当前脚本的绝对路径
# os.path.dirname(...) → 去掉文件名，得到 scripts/ 目录
# 再 dirname 一次 → 得到项目根目录，这样才能正确找到
# Add project root to Python search path
# This script is in scripts/ subfolder, Python can't find backend module by default
# This ensures that the project root is found correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import db
from backend.app.models import Movie

# Genre Mapping Table
#In MovieLens 100k, each movie's genre is represented by 19 binary flags (0 or 1)
# e.g. [0,1,1,0,...] means 2nd=Action, 3rd=Adventure → "Action|Adventure"
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
    Parse genre flags (list of 0/1) into genre name string

    参数:
        genre_flags: 长度为19的列表，包含0或1

    返回:
        类型名称字符串，用 | 分隔，例如 "Animation|Comedy|Children's"
    """
    genres = []
    # 枚举从1开始编号，刚好对应 GENRE_MAP 的 key
    # enumerate with start=1, matches GENRE_MAP keys
    for i, flag in enumerate(genre_flags, start=1):
        if flag == '1' or flag == 1:
            genre_name = GENRE_MAP.get(i)
            if genre_name:
                genres.append(genre_name)
    # 用 '|' 拼接所有类型名，如果一部都没有就返回 'unknown'
    # Join all genre names with '|', return 'unknown' if none found
    return '|'.join(genres) if genres else 'unknown'


def import_movies(file_path):
    """
    导入电影数据到数据库
    Import movie data into database

    参数:
        file_path: u.item 文件的路径
    """
    print(f"正在读取电影数据: {file_path}")

    # 连接数据库 Open database connection
    db.connect()

    # 统计计数器 / Counters
    total = 0  # 总处理行数 / Total rows processed
    inserted = 0  # 新增条数 / Newly inserted count
    updated = 0  # 更新条数 / Updated count

    with open(file_path, 'r', encoding='latin-1') as f:  # Open file with latin-1 encoding
        reader = csv.reader(f, delimiter='|')#use "|" to delimit fields

        for row in reader:
            total += 1
            movie_id = int(row[0])# 第1列：电影ID / Column 1: Movie ID
            title = row[1]# 第2列：电影标题 / Column 2: Movie title
            # 第6~24列（索引5~23）：19个类型标记，每个是0或1
            # Columns 6-24 (index 5-23): 19 genre flags, each 0 or 1
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
                # 已存在 → 更新标题和类型 / Already exists → update title and genres
                movie.title = title
                movie.genres = genres_str
                movie.save()
                updated += 1
            else:
                inserted += 1

            # 每处理100条打印一次进度，防止大文件导入时看不到进度
            # Print progress every 100 rows, so we can monitor long imports
            if total % 100 == 0:
                print(f"已处理 {total} 条...")

    print(f"\n导入完成！")
    print(f"总处理: {total} 条")
    print(f"新增: {inserted} 条")
    print(f"更新: {updated} 条")

    db.close()



if __name__ == "__main__":
    # 注意修改为 u.item 文件实际路径
    DATA_PATH = r"C:\Users\pluck\Desktop\ml-100k\u.item"

    # 检查文件是否存在
    if not os.path.exists(DATA_PATH):
        print(f"错误: 找不到文件 {DATA_PATH}")
        print("请修改 DATA_PATH 变量为你的 u.item 文件路径")
        sys.exit(1)# sys.exit(1) 表示异常退出 / Exit with error code

    import_movies(DATA_PATH)