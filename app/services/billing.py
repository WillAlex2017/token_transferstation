from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_config import ModelConfig
from app.models.usage_log import UsageLog
from app.models.user import User


async def deduct_balance(
    session: AsyncSession,
    user: User,
    amount: Decimal,
) -> bool:
    if user.balance < amount:
        return False
    user.balance -= amount
    session.add(user)
    return True


async def calculate_cost(
    session: AsyncSession,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> tuple[Decimal, Decimal]:
    result = await session.execute(
        select(ModelConfig).where(ModelConfig.name == model_name)
    )
    model = result.scalar_one_or_none()
    if not model:
        return Decimal("0"), Decimal("0")

    cost = (
        Decimal(str(prompt_tokens)) * model.sell_input_price
        + Decimal(str(completion_tokens)) * model.sell_output_price
    )
    provider_cost = (
        Decimal(str(prompt_tokens)) * model.input_price
        + Decimal(str(completion_tokens)) * model.output_price
    )
    return cost, provider_cost


async def log_usage(
    session: AsyncSession,
    user_id,
    api_key_id,
    model_id,
    prompt_tokens: int,
    completion_tokens: int,
    cost: Decimal,
    provider_cost: Decimal,
    status: str = "success",
):
    log = UsageLog(
        user_id=user_id,
        api_key_id=api_key_id,
        model_id=model_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost=cost,
        provider_cost=provider_cost,
        profit=cost - provider_cost,
        status=status,
    )
    session.add(log)
    return log
