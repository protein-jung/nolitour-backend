from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://nolitour:nolitour@localhost:5432/nolitour"

    naver_map_client_id: str = ""
    naver_map_client_secret: str = ""

    public_data_api_key: str = ""

    frontend_origin: str = "http://localhost:5173"

    slack_webhook_url: str = ""

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    storage_backend: str = "local"  # local | s3 (s3 to be implemented later)
    media_root: str = "media"
    media_url_prefix: str = "/media"


settings = Settings()
