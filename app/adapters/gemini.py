import json

import httpx

from app.adapters.base import BaseAdapter


class GeminiAdapter(BaseAdapter):
    async def chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs,
    ):
        base = self.base_url.rstrip("/") if self.base_url else "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base}/models/{model}:generateContent?key={self.api_key}"

        headers = {"Content-Type": "application/json"}

        gemini_messages = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_instruction = content
            else:
                gemini_role = "user" if role == "user" else "model"
                gemini_messages.append({"role": gemini_role, "parts": [{"text": content}]})

        payload = {"contents": gemini_messages}
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        generation_config = {"temperature": temperature}
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens
        payload["generationConfig"] = generation_config

        if stream:
            payload["generationConfig"]["candidateCount"] = 1

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                yield {"type": "error", "data": {"status": resp.status_code, "detail": detail}}
                return

            data = resp.json()

            if not data.get("candidates"):
                yield {"type": "error", "data": {"status": 500, "detail": "No candidates returned"}}
                return

            candidate = data["candidates"][0]
            content_text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

            prompt_tokens = data.get("usageMetadata", {}).get("promptTokenCount", 0)
            completion_tokens = data.get("usageMetadata", {}).get("candidatesTokenCount", 0)

            openai_response = {
                "id": data.get("id", f"chatcmpl-{httpx._utils.get_unique_id()}"),
                "object": "chat.completion",
                "created": int(httpx._time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content_text},
                        "finish_reason": candidate.get("finishReason", "stop"),
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }

            yield {"type": "complete", "data": openai_response}

    async def embeddings(self, input: list[str], model: str, **kwargs) -> list[list[float]]:
        base = self.base_url.rstrip("/") if self.base_url else "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base}/models/{model}:embedContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        if len(input) > 1:
            raise ValueError("Gemini embeddings currently supports only one text at a time")

        payload = {"content": {"parts": [{"text": input[0]}]}}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return [data["embedding"]["values"]]

    async def count_tokens(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(msg.get("content", "")) // 4
        return total