from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseAdapter(ABC):
    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs,
    ) -> AsyncGenerator[dict, None]:
        ...

    @abstractmethod
    async def embeddings(
        self,
        input: list[str],
        model: str,
        **kwargs,
    ) -> list[list[float]]:
        ...

    @abstractmethod
    async def count_tokens(self, messages: list[dict]) -> int:
        ...
