from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://admin:admin123@localhost:5432/token_transfer"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-to-a-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    qwen_api_key: str = ""
    gemini_api_key: str = ""
    nvidia_api_key: str = ""
    xai_api_key: str = ""
    groq_api_key: str = ""
    baichuan_api_key: str = ""
    zhipu_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
