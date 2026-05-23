from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o", "object": "model", "created": 1700000000, "owned_by": "openai"},
            {"id": "gpt-4o-mini", "object": "model", "created": 1700000000, "owned_by": "openai"},
            {"id": "claude-3.5-sonnet", "object": "model", "created": 1700000000, "owned_by": "anthropic"},
            {"id": "deepseek-v3", "object": "model", "created": 1700000000, "owned_by": "deepseek"},
            {"id": "deepseek-r1", "object": "model", "created": 1700000000, "owned_by": "deepseek"},
            {"id": "qwen-max", "object": "model", "created": 1700000000, "owned_by": "qwen"},
            {"id": "gemini-2.0-flash", "object": "model", "created": 1700000000, "owned_by": "google"},
        ]
    }
