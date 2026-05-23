from fastapi import APIRouter, Depends

from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completion(
    request: ChatCompletionRequest,
):
    return ChatCompletionResponse(
        id="chatcmpl-mock",
        created=1700000000,
        model=request.model,
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": "Hello from Token Transfer Station!"},
            "finish_reason": "stop",
        }],
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )


@router.post("/embeddings")
async def embeddings(
    request: dict,
):
    return {"object": "list", "data": [], "model": request.get("model", ""), "usage": {"prompt_tokens": 0, "total_tokens": 0}}
