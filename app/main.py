from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1 import admin, chat, models, user
from app.config import settings
from app.database import Base, async_session_factory, engine
from app.middleware.auth import AuthMiddleware
from app.middleware.billing import BillingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.models.model_config import ModelConfig
from app.models.user import User
from app.services.auth import hash_password

SEED_MODELS = [
    ModelConfig(name="gpt-4o-mini", provider="openai", upstream_model="gpt-4o-mini", input_price=0.00000015, output_price=0.0000006, sell_input_price=0.0000002, sell_output_price=0.0000008),
    ModelConfig(name="llama-3.1-70b", provider="nvidia", upstream_model="meta/llama-3.1-70b-instruct", input_price=0.0000005, output_price=0.0000015, sell_input_price=0.0000007, sell_output_price=0.000002),
    ModelConfig(name="llama-3.3-70b", provider="nvidia", upstream_model="meta/llama-3.3-70b-instruct", input_price=0.0000003, output_price=0.000001, sell_input_price=0.0000005, sell_output_price=0.0000015),
    ModelConfig(name="glm-4-flash", provider="zhipu", upstream_model="glm-4-flash", input_price=0.0000001, output_price=0.0000001, sell_input_price=0.00000015, sell_output_price=0.00000015),
    ModelConfig(name="glm-4-plus", provider="zhipu", upstream_model="glm-4-plus", input_price=0.0000005, output_price=0.0000005, sell_input_price=0.0000007, sell_output_price=0.0000007),
    ModelConfig(name="glm-4-air", provider="zhipu", upstream_model="glm-4-air", input_price=0.00000025, output_price=0.00000025, sell_input_price=0.00000035, sell_output_price=0.00000035),
]


async def seed_data():
    async with async_session_factory() as session:
        result = await session.execute(select(ModelConfig).limit(1))
        if not result.scalar_one_or_none():
            for m in SEED_MODELS:
                session.add(m)
            await session.commit()

        result = await session.execute(select(User).where(User.email == settings.admin_email))
        if not result.scalar_one_or_none():
            admin = User(
                email=settings.admin_email,
                name="Admin",
                hashed_password=hash_password(settings.admin_password),
                role="admin",
            )
            session.add(admin)
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()
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

app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(user.router)

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    html = STATIC_DIR / "index.html"
    if html.exists():
        return FileResponse(str(html))
    return {"message": "Token Transfer Station API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
