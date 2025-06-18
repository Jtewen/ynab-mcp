from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Defines the application settings.
    Reads configuration from environment variables or a .env file.
    """

    ynab_api_token: str = Field(..., alias="YNAB_PAT")
    """The API token for authenticating with the YNAB API."""

    model_config = SettingsConfigDict(
        env_file="/home/jewen/mcp/ynab-mcp/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
