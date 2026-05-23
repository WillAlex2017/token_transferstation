from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chat, models, user
from app.database import Base, engine
from app.middleware.auth import AuthMiddleware
from app.middleware.billing import BillingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Token Transfer Station",
    description="LLM API Token 中转站 - 统一接入国内外大模型",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(BillingMiddleware)

app.include_router(chat.router)
app.include_router(models.router)
app.include_router(user.router)


@app.get("/")
async def root():
    return {"message": "Token Transfer Station API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
