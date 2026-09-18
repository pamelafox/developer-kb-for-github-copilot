import os
from dataclasses import dataclass

from dotenv_azd import load_azd_env


def is_running_in_production() -> bool:
    return os.getenv("RUNNING_IN_PRODUCTION", "").lower() in {"1", "true", "yes"}


def load_local_environment() -> None:
    if not is_running_in_production():
        load_azd_env(quiet=True)


@dataclass(frozen=True)
class Settings:
    search_endpoint: str
    openai_endpoint: str
    embedding_deployment: str
    embedding_model: str
    chat_deployment: str
    chat_model: str
    managed_identity_client_id: str | None
    storage_account_name: str = ""
    content_understanding_deployment: str = "gpt-5.4-mini"
    content_understanding_model: str = "gpt-5.4-mini"

    @classmethod
    def from_environment(cls) -> "Settings":
        load_local_environment()
        return cls(
            search_endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/"),
            openai_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/"),
            embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
            embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.4-mini"),
            chat_model=os.getenv("AZURE_OPENAI_CHAT_MODEL", "gpt-5.4-mini"),
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID"),
            storage_account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
            content_understanding_deployment=os.getenv(
                "AZURE_CONTENT_UNDERSTANDING_DEPLOYMENT", "gpt-5.4-mini"
            ),
            content_understanding_model=os.getenv("AZURE_CONTENT_UNDERSTANDING_MODEL", "gpt-5.4-mini"),
        )