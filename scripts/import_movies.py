import csv
from backend.app.database import db
from backend.app.models import Movie

# 连接数据库
db.connect()

# 读取 u.item 文件
with open('C:/Users/LIANXIANG/Desktop/ml-100k/ml-100k/u.item', 'r', encoding='latin-1') as f:
    reader = csv.reader(f, delimiter='|')
    for row in reader:
        movie_id = int(row[0])
        title = row[1]
        # 去掉标题中的年份（可选）
        # 这里简单处理
        genres = row[5:]  # 5-23是类型，可以组合成一个字符串
        genres_str = '|'.join([g for i, g in enumerate(genres) if g == '1'])

        # 插入或忽略重复
        Movie.get_or_create(id=movie_id, defaults={'title': title, 'genres': genres_str})

print("电影数据导入完成")
db.close()