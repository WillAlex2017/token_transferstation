import json

import httpx

from app.adapters.base import BaseAdapter


class ZhipuAdapter(BaseAdapter):
    async def chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs,
    ):
        base = self.base_url.rstrip("/") if self.base_url else "https://open.bigmodel.cn/api/paas/v4"
        url = f"{base}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            if stream:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield {"type": "error", "data": {"status": response.status_code, "detail": body.decode()}}
                        return
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                yield {"type": "done"}
                            else:
                                yield {"type": "chunk", "data": json.loads(data)}
            else:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    try:
                        detail = resp.json()
                    except Exception:
                        detail = resp.text
                    yield {"type": "error", "data": {"status": resp.status_code, "detail": detail}}
                    return
                yield {"type": "complete", "data": resp.json()}

    async def embeddings(self, input: list[str], model: str, **kwargs) -> list[list[float]]:
        base = self.base_url.rstrip("/") if self.base_url else "https://open.bigmodel.cn/api/paas/v4"
        url = f"{base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "input": input, **kwargs}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    async def count_tokens(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(msg.get("content", "")) // 4
        return total