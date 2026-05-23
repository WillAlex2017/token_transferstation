from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.model_config import ModelConfig
from app.models.usage_log import UsageLog
from app.models.user import User

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user_count = (await db.execute(select(func.count(User.id)))).scalar()
    total_calls = (await db.execute(select(func.count(UsageLog.id)))).scalar()
    total_cost = (await db.execute(select(func.coalesce(func.sum(UsageLog.cost), 0)))).scalar()
    total_profit = (await db.execute(select(func.coalesce(func.sum(UsageLog.profit), 0)))).scalar()
    active_keys = (await db.execute(select(func.count(ApiKey.id)).where(ApiKey.status == "active"))).scalar()
    return {
        "user_count": user_count,
        "total_calls": total_calls,
        "total_cost": float(total_cost),
        "total_profit": float(total_profit),
        "active_keys": active_keys,
    }


@router.get("/users")
async def admin_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "balance": float(u.balance),
            "status": u.status,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.put("/users/{user_id}/status")
async def admin_update_user_status(
    user_id: str,
    body: dict,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_status = body.get("status")
    if new_status not in ("active", "disabled"):
        raise HTTPException(status_code=400, detail="Invalid status")
    user.status = new_status
    db.add(user)
    return {"message": f"User {user_id} status set to {new_status}"}


@router.post("/users/{user_id}/topup")
async def admin_topup_user(
    user_id: str,
    body: dict,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    amount = body.get("amount", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    user.balance = float(user.balance) + amount
    db.add(user)
    return {"message": f"Topup {amount} to {user.email}", "balance": float(user.balance)}


@router.get("/models")
async def admin_models(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ModelConfig).order_by(ModelConfig.name))
    models = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "provider": m.provider,
            "upstream_model": m.upstream_model,
            "input_price": float(m.input_price),
            "output_price": float(m.output_price),
            "sell_input_price": float(m.sell_input_price),
            "sell_output_price": float(m.sell_output_price),
            "status": m.status,
        }
        for m in models
    ]


@router.put("/models/{model_id}/status")
async def admin_update_model_status(
    model_id: str,
    body: dict,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    new_status = body.get("status")
    if new_status not in ("active", "disabled"):
        raise HTTPException(status_code=400, detail="Invalid status")
    model.status = new_status
    db.add(model)
    return {"message": f"Model {model.name} status set to {new_status}"}


@router.put("/models/{model_id}/price")
async def admin_update_model_price(
    model_id: str,
    body: dict,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if "sell_input_price" in body:
        model.sell_input_price = body["sell_input_price"]
    if "sell_output_price" in body:
        model.sell_output_price = body["sell_output_price"]
    if "input_price" in body:
        model.input_price = body["input_price"]
    if "output_price" in body:
        model.output_price = body["output_price"]
    db.add(model)
    return {"message": f"Model {model.name} prices updated"}


@router.get("/usage")
async def admin_usage(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(UsageLog).order_by(UsageLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "user_id": str(log.user_id),
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "cost": float(log.cost),
            "profit": float(log.profit),
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
