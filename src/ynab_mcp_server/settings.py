from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Defines the application settings.
    Reads configuration from environment variables or a .env file.
    """

    ynab_api_token: str = Field(..., alias="YNAB_PAT")
    """The API token for authenticating with the YNAB API."""

    ynab_default_budget_id: Optional[str] = Field(
        None, alias="YNAB_DEFAULT_BUDGET_ID"
    )
    """If set, the server will operate in single-budget mode with this budget ID."""

    ynab_read_only: bool = Field(False, alias="YNAB_READ_ONLY")
    """If true, the server will operate in read-only mode."""

    model_config = SettingsConfigDict(
        env_file="/home/jewen/mcp/ynab-mcp/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
