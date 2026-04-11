from app.v1.config import settings
from sqlmodel import create_engine


DATABASE_URL=f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)