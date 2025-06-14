from sqlalchemy import create_engine, Integer
from sqlalchemy.sql import text
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем параметры подключения к базе данных
POSTGRES_USER = "postgres"  # Используем postgres пользователя для миграции
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Формируем строку подключения
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

def upgrade():
    """Add time_offset column to stations table"""
    engine = create_engine(DATABASE_URL)
    
    # Добавляем колонку time_offset
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE stations 
            ADD COLUMN time_offset INTEGER DEFAULT 0;
        """))
        conn.commit()

def downgrade():
    """Remove time_offset column from stations table"""
    engine = create_engine(DATABASE_URL)
    
    # Удаляем колонку time_offset
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE stations 
            DROP COLUMN time_offset;
        """))
        conn.commit()

if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully!") 