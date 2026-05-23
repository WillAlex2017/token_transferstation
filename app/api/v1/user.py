from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.user import (
    ApiKeyResponse,
    BalanceResponse,
    CreateApiKeyRequest,
    TokenResponse,
    TopUpRequest,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth import create_access_token, generate_api_key, hash_password, verify_password

router = APIRouter(prefix="/v1/user", tags=["user"])


@router.post("/register", response_model=UserResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        balance=float(user.balance),
        status=user.status,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/profile", response_model=UserResponse)
async def profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        balance=float(current_user.balance),
        status=current_user.status,
        created_at=current_user.created_at,
    )


@router.get("/balance", response_model=BalanceResponse)
async def balance(current_user: User = Depends(get_current_user)):
    return BalanceResponse(balance=float(current_user.balance))


@router.post("/topup", response_model=BalanceResponse)
async def topup(
    body: TopUpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    current_user.balance = float(current_user.balance) + body.amount
    db.add(current_user)
    return BalanceResponse(balance=float(current_user.balance))


@router.get("/usage", response_model=list[dict])
async def usage_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == current_user.id)
        .order_by(UsageLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "model_id": str(log.model_id),
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "cost": float(log.cost),
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    body: CreateApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    api_key = ApiKey(
        user_id=current_user.id,
        key=generate_api_key(),
        name=body.name,
    )
    db.add(api_key)
    await db.flush()
    return ApiKeyResponse(
        id=str(api_key.id),
        key=api_key.key,
        name=api_key.name,
        status=api_key.status,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == current_user.id,
            ApiKey.status == "active",
        )
    )
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=str(k.id),
            key=k.key,
            name=k.name,
            status=k.status,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.status = "revoked"
    db.add(api_key)
    return {"message": "API key revoked"}
