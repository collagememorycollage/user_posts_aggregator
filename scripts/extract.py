#!/opt/venv/bin/python
import os
import requests
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# ==== Настройки подключения ====
DB_USER = os.environ.get("POSTGRES_USER", "myuser")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "mypassword")
DB_NAME = os.environ.get("POSTGRES_DB", "mydatabase")
DB_HOST = os.environ.get("POSTGRES_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
API_URL = "https://jsonplaceholder.typicode.com/todos"

# ==== SQLAlchemy ====
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ==== Таблица raw_users_by_posts ====
class RawUserByPost(Base):
    __tablename__ = "raw_users_by_posts"
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    completed = Column(Boolean, nullable=False)

# ==== Создание таблицы, если нет ====
Base.metadata.create_all(engine, checkfirst=True)
print("Таблица raw_users_by_posts создана или уже существует")

# ==== Получение данных из API ====
try:
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    print(f"Получено {len(data)} записей из API")
except requests.RequestException as e:
    print(f"Ошибка при подключении к API: {e}")
    exit(1)

# ==== Загрузка данных ====
with Session() as session:
    try:
        existing_ids = {r.id for r in session.query(RawUserByPost.id).all()}

        new_records = [
            RawUserByPost(
                id=item["id"],
                userId=item["userId"],
                title=item["title"],
                completed=item["completed"]
            )
            for item in data if item["id"] not in existing_ids
        ]

        if new_records:
            session.bulk_save_objects(new_records)
            session.commit()
            print(f"Добавлено {len(new_records)} новых записей")
        else:
            print("Новых записей нет")

    except Exception as e:
        session.rollback()
        print(f"Ошибка при загрузке данных: {e}")

