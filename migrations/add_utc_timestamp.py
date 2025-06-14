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
    """Add timestamp_utc columns to water_levels and temperatures tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Добавляем колонку timestamp_utc в таблицу water_levels
        conn.execute(text("""
            ALTER TABLE water_levels 
            ADD COLUMN timestamp_utc TIMESTAMP;
        """))
        
        # Добавляем колонку timestamp_utc в таблицу temperatures
        conn.execute(text("""
            ALTER TABLE temperatures 
            ADD COLUMN timestamp_utc TIMESTAMP;
        """))
        
        # Обновляем timestamp_utc в water_levels, используя time_offset из stations (по умолчанию 0)
        conn.execute(text("""
            UPDATE water_levels wl
            SET timestamp_utc = wl.timestamp + (COALESCE(s.time_offset, 0) || ' seconds')::interval
            FROM stations s
            WHERE wl.station_id = s.id;
        """))
        
        # Обновляем timestamp_utc в temperatures, используя time_offset из stations (по умолчанию 0)
        conn.execute(text("""
            UPDATE temperatures t
            SET timestamp_utc = t.timestamp + (COALESCE(s.time_offset, 0) || ' seconds')::interval
            FROM stations s
            WHERE t.station_id = s.id;
        """))
        
        conn.commit()

def downgrade():
    """Remove timestamp_utc columns from water_levels and temperatures tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Удаляем колонку timestamp_utc из таблицы water_levels
        conn.execute(text("""
            ALTER TABLE water_levels 
            DROP COLUMN timestamp_utc;
        """))
        
        # Удаляем колонку timestamp_utc из таблицы temperatures
        conn.execute(text("""
            ALTER TABLE temperatures 
            DROP COLUMN timestamp_utc;
        """))
        
        conn.commit()

if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully!") 