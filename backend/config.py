from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MakeItHappen configuration — loaded from environment or .env file."""

    anthropic_api_key: str = ""

    # Model assignments per role (use exact model IDs)
    model_orchestrator: str = "claude-opus-4-6"
    model_engineer: str = "claude-opus-4-6"
    model_classifier: str = "claude-haiku-4-5"
    model_translator: str = "claude-sonnet-4-6"
    model_ceo_filter: str = "claude-sonnet-4-6"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Agent defaults
    max_agent_turns: int = 25

    # GitHub integration — push generated projects to repos
    github_token: str = ""
    github_owner: str = ""  # GitHub user or org to create repos under

    # Project defaults
    default_project_dir: str = "."

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
