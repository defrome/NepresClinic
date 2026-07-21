from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nepres_clinic.db"
    jwt_secret: str = "development-only-change-me"
    jwt_expire_minutes: int = 480
    seed_demo_data: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
