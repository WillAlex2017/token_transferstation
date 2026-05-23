from app.adapters import BaseAdapter, OpenAIAdapter


class ModelRouter:
    adapter_map: dict[str, type[BaseAdapter]] = {
        "openai": OpenAIAdapter,
        "anthropic": OpenAIAdapter,
        "deepseek": OpenAIAdapter,
        "qwen": OpenAIAdapter,
        "gemini": OpenAIAdapter,
        "google": OpenAIAdapter,
    }

    def get_adapter(self, provider: str, api_key: str, base_url: str | None = None) -> BaseAdapter:
        adapter_cls = self.adapter_map.get(provider, OpenAIAdapter)
        return adapter_cls(api_key=api_key, base_url=base_url)


router = ModelRouter()
