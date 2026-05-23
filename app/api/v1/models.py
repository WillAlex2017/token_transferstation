from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model_config import ModelConfig

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.status == "active")
    )
    models = result.scalars().all()
    return {
        "object": "list",
        "data": [
            {"id": m.name, "object": "model", "owned_by": m.provider}
            for m in models
        ],
    }
