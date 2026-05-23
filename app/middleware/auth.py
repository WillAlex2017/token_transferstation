from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC_PATHS = {"/v1/models", "/v1/user/register", "/v1/user/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/v1/") and path not in PUBLIC_PATHS:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
            request.state.api_key = auth_header[7:]
        return await call_next(request)
