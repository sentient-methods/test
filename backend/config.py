from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MakeItHappen configuration — loaded from environment or .env file."""

    anthropic_api_key: str = ""

    # Model assignments per role
    model_orchestrator: str = "claude-opus-4-6"
    model_engineer: str = "claude-opus-4-6"
    model_classifier: str = "claude-haiku-4-5-20251001"
    model_translator: str = "claude-sonnet-4-6"
    model_ceo_filter: str = "claude-sonnet-4-6"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Agent defaults
    max_agent_turns: int = 25

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
