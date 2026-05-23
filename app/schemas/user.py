from datetime import datetime

from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    balance: float
    status: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateApiKeyRequest(BaseModel):
    name: str = "Default"


class ApiKeyResponse(BaseModel):
    id: str
    key: str
    name: str
    status: str
    created_at: datetime


class BalanceResponse(BaseModel):
    balance: float


class TopUpRequest(BaseModel):
    amount: float
