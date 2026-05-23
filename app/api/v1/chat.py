import json
import time
import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.deps import get_current_user
from app.adapters.openai import OpenAIAdapter
from app.config import settings
from app.database import get_db
from app.models.model_config import ModelConfig
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.chat import ChatCompletionRequest

router = APIRouter(prefix="/v1", tags=["chat"])

PROVIDER_API_KEY_MAP = {
    "openai": ("openai_api_key", None),
    "anthropic": ("anthropic_api_key", None),
    "deepseek": ("deepseek_api_key", "https://api.deepseek.com"),
    "qwen": ("qwen_api_key", None),
    "google": ("gemini_api_key", None),
    "nvidia": ("nvidia_api_key", "https://integrate.api.nvidia.com"),
}


async def get_model_config(db: AsyncSession, model_name: str) -> ModelConfig | None:
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.name == model_name, ModelConfig.status == "active")
    )
    return result.scalar_one_or_none()


async def log_and_bill(
    db: AsyncSession,
    user: User,
    api_key_id: str | None,
    model: ModelConfig,
    prompt_tokens: int,
    completion_tokens: int,
    status: str = "success",
):
    cost = Decimal(str(prompt_tokens)) * model.sell_input_price + Decimal(str(completion_tokens)) * model.sell_output_price
    provider_cost = Decimal(str(prompt_tokens)) * model.input_price + Decimal(str(completion_tokens)) * model.output_price

    user.balance = float(Decimal(str(user.balance)) - cost)
    db.add(user)

    log = UsageLog(
        user_id=user.id,
        api_key_id=UUID(api_key_id) if api_key_id else None,
        model_id=model.id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost=cost,
        provider_cost=provider_cost,
        profit=cost - provider_cost,
        status=status,
    )
    db.add(log)


@router.post("/chat/completions")
async def chat_completion(
    body: ChatCompletionRequest,
    http_request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    model = await get_model_config(db, body.model)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{body.model}' not found")

    key_field, base_url = PROVIDER_API_KEY_MAP.get(model.provider, (None, None))
    if not key_field:
        raise HTTPException(status_code=500, detail=f"No upstream config for provider '{model.provider}'")

    upstream_key = getattr(settings, key_field, "")
    if not upstream_key:
        raise HTTPException(status_code=502, detail=f"Upstream API key for '{model.provider}' not configured")

    api_key_id = getattr(http_request.state, "_api_key_id", None)

    if body.stream:
        return await _chat_stream(body, model, upstream_key, base_url, user, db, api_key_id)

    return await _chat_non_stream(body, model, upstream_key, base_url, user, db, api_key_id)


async def _chat_non_stream(body, model, upstream_key, base_url, user, db, api_key_id):
    adapter = OpenAIAdapter(api_key=upstream_key, base_url=base_url)
    gen = adapter.chat_completion(
        messages=[m.model_dump() for m in body.messages],
        model=model.upstream_model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        stream=False,
    )
    result = None
    async for chunk in gen:
        if chunk["type"] == "complete":
            result = chunk["data"]
        elif chunk["type"] == "error":
            raise HTTPException(
                status_code=chunk["data"].get("status", 502),
                detail=f"Upstream error: {chunk['data'].get('detail', 'unknown')}",
            )

    if not result:
        raise HTTPException(status_code=502, detail="Upstream returned empty response")

    usage = result.get("usage", {})
    pt = usage.get("prompt_tokens", 0)
    ct = usage.get("completion_tokens", 0)

    await log_and_bill(db, user, api_key_id, model, pt, ct)

    return {
        "id": result.get("id", f"chatcmpl-{uuid.uuid4().hex[:12]}"),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.model,
        "choices": [
            {
                "index": ch["index"],
                "message": {
                    "role": ch["message"]["role"],
                    "content": ch["message"]["content"],
                },
                "finish_reason": ch.get("finish_reason", "stop"),
            }
            for ch in result.get("choices", [])
        ],
        "usage": {
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": pt + ct,
        },
    }


async def _chat_stream(body, model, upstream_key, base_url, user, db, api_key_id):
    adapter = OpenAIAdapter(api_key=upstream_key, base_url=base_url)

    async def generate():
        gen = adapter.chat_completion(
            messages=[m.model_dump() for m in body.messages],
            model=model.upstream_model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            stream=True,
        )
        pt = 0
        ct = 0
        async for chunk in gen:
            if chunk["type"] == "chunk":
                data = chunk["data"]
                if data.get("usage"):
                    pt = data["usage"].get("prompt_tokens", 0)
                    ct = data["usage"].get("completion_tokens", 0)
                data["model"] = body.model
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "done":
                yield "data: [DONE]\n\n"

        await log_and_bill(db, user, api_key_id, model, pt, ct)

    return StreamingResponse(generate(), media_type="text/event-stream")
