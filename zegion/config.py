"""
Configuration file for paths and Notion API credentials.

Replace with your own paths and API credentials.
"""

from deepmerge import always_merger
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotionConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow", env_prefix="NOTION_", env_file=".env"
    )

    api_key: str | None = ""
    parent_page_id: str | None = ""


class OpenAIConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow", env_prefix="OPENAI_", env_file=".env"
    )

    default_model: str | None = "gpt-4o-mini"


class Config(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    notion: NotionConfig = NotionConfig()
    openai: OpenAIConfig = OpenAIConfig()

    def __lshift__(self, other: "Config") -> "Config":
        base = self.model_dump(exclude_unset=True)
        nxt = other.model_dump(exclude_unset=True, exclude_none=True)
        new = Config(**always_merger.merge(base, nxt))
        self.notion = new.notion
        self.openai = new.openai
        return self


config = Config()


##########
# Notion #
##########


def get_notion_config() -> NotionConfig:
    return config.notion


##########
# OpenAI #
##########


def get_openai_config() -> OpenAIConfig:
    return config.openai


def get_default_openai_model() -> str:
    return get_openai_config().default_model


def load_config(new_config: Config) -> Config:
    return config << new_config
