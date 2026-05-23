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
    ModelConfig(name="gpt-4o", provider="openai", upstream_model="gpt-4o", input_price=0.0000025, output_price=0.00001, sell_input_price=0.0000035, sell_output_price=0.000014),
    ModelConfig(name="gpt-4o-mini", provider="openai", upstream_model="gpt-4o-mini", input_price=0.00000015, output_price=0.0000006, sell_input_price=0.0000002, sell_output_price=0.0000008),
    ModelConfig(name="claude-3.5-sonnet", provider="anthropic", upstream_model="claude-3-5-sonnet-20241022", input_price=0.000003, output_price=0.000015, sell_input_price=0.0000042, sell_output_price=0.000021),
    ModelConfig(name="deepseek-v3", provider="deepseek", upstream_model="deepseek-chat", input_price=0.00000027, output_price=0.0000011, sell_input_price=0.00000035, sell_output_price=0.0000015),
    ModelConfig(name="deepseek-r1", provider="deepseek", upstream_model="deepseek-reasoner", input_price=0.00000055, output_price=0.00000219, sell_input_price=0.00000075, sell_output_price=0.000003),
    ModelConfig(name="qwen-max", provider="qwen", upstream_model="qwen-max", input_price=0.00000004, output_price=0.00000012, sell_input_price=0.00000005, sell_output_price=0.00000016),
    ModelConfig(name="gemini-2.0-flash", provider="google", upstream_model="gemini-2.0-flash", input_price=0.0000001, output_price=0.0000004, sell_input_price=0.00000015, sell_output_price=0.0000006),
    ModelConfig(name="llama-3.1-70b", provider="nvidia", upstream_model="meta/llama-3.1-70b-instruct", input_price=0.0000005, output_price=0.0000015, sell_input_price=0.0000007, sell_output_price=0.000002),
    ModelConfig(name="llama-3.3-70b", provider="nvidia", upstream_model="meta/llama-3.3-70b-instruct", input_price=0.0000003, output_price=0.000001, sell_input_price=0.0000005, sell_output_price=0.0000015),
    ModelConfig(name="grok-beta", provider="xai", upstream_model="grok-beta", input_price=0.0000001, output_price=0.0000004, sell_input_price=0.00000015, sell_output_price=0.0000006),
    ModelConfig(name="grok-2", provider="xai", upstream_model="grok-2-1212", input_price=0.0000001, output_price=0.0000004, sell_input_price=0.00000015, sell_output_price=0.0000006),
    ModelConfig(name="llama-3.1-70b-ssoa", provider="groq", upstream_model="llama-3.1-70b-versatile", input_price=0.00000009, output_price=0.00000012, sell_input_price=0.00000012, sell_output_price=0.00000015),
    ModelConfig(name="mixtral-8x7b-32768", provider="groq", upstream_model="mixtral-8x7b-32768", input_price=0.00000009, output_price=0.00000012, sell_input_price=0.00000012, sell_output_price=0.00000015),
    ModelConfig(name="gemma2-9b-it", provider="groq", upstream_model="gemma2-9b-it", input_price=0.00000009, output_price=0.00000012, sell_input_price=0.00000012, sell_output_price=0.00000015),
    ModelConfig(name="baichuan4", provider="baichuan", upstream_model="Baichuan4", input_price=0.0000001, output_price=0.0000004, sell_input_price=0.00000015, sell_output_price=0.0000006),
    ModelConfig(name="baichuan-turbo", provider="baichuan", upstream_model="Baichuan4-Turbo", input_price=0.00000009, output_price=0.00000012, sell_input_price=0.00000012, sell_output_price=0.00000015),
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
