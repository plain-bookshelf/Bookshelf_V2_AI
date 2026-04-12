import os
from pydantic_settings import BaseSettings, SettingsConfigDict

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(app_dir) # 한 번 더 올라감
env_path = os.path.join(root_dir, ".env")

class Settings(BaseSettings):
    BIG_API_KEY : str
    SMALL_API_KEY : str
    SECRET_KEY : str
    MODEL_1 : str
    MODEL_2 : str
    MODEL_3: str
    BASE_URL : str

    DB_USER : str
    DB_PASSWORD : str
    DB_HOST : str
    DB_PORT : str
    DB_NAME : str

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8"
    )

settings = Settings()