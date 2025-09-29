#!/opt/venv/bin/python
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime, func, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
import sys
import time

# ==== Настройки подключения ====
DB_USER = os.environ.get("POSTGRES_USER", "myuser")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "mypassword")
DB_NAME = os.environ.get("POSTGRES_DB", "mydatabase")
DB_HOST = os.environ.get("POSTGRES_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ==== SQLAlchemy ====
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()
inspector = inspect(engine)

# ==== Существующая таблица raw_users_by_posts ====
class RawUserByPost(Base):
    __tablename__ = "raw_users_by_posts"
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, nullable=False)

# ==== Новая таблица top_users_by_posts ====
class TopUsersByPosts(Base):
    __tablename__ = "top_users_by_posts"
    user_id = Column(Integer, primary_key=True)
    posts_cnt = Column(Integer, nullable=False)
    calculated_at = Column(DateTime, nullable=False)

# ==== Проверка наличия исходной таблицы ====
MAX_RETRIES = 5
for attempt in range(MAX_RETRIES):
    if inspector.has_table("raw_users_by_posts"):
        print("Таблица raw_users_by_posts найдена")
        break
    else:
        print(f"Таблица raw_users_by_posts не найдена, пробуем ещё раз ({attempt+1}/{MAX_RETRIES})...")
        time.sleep(2)  # ждём 2 секунды
else:
    print("Таблица raw_users_by_posts не существует. Сначала запустите extract.py")
    sys.exit(1)

# ==== Создание таблицы top_users_by_posts, если нет ====
TopUsersByPosts.__table__.create(bind=engine, checkfirst=True)
print("Таблица top_users_by_posts создана или уже существует")

# ==== Агрегация и вставка данных ====
with Session() as session:
    try:
        aggregated_data = (
            session.query(
                RawUserByPost.userId.label("user_id"),
                func.count(RawUserByPost.id).label("posts_cnt")
            )
            .group_by(RawUserByPost.userId)
            .all()
        )

        if not aggregated_data:
            print("Нет данных для вставки")
        else:
            now = datetime.utcnow()

            # Очистка таблицы перед вставкой
            session.query(TopUsersByPosts).delete()

            # Подготовка и пакетная вставка данных
            rows = [
                TopUsersByPosts(
                    user_id=row.user_id,
                    posts_cnt=row.posts_cnt,
                    calculated_at=now
                )
                for row in aggregated_data
            ]

            session.bulk_save_objects(rows)
            session.commit()
            print(f"Вставлено {len(rows)} строк в top_users_by_posts")

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при вставке данных: {e}")

