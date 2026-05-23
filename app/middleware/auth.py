from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            request.state.token = auth[7:]
        response = await call_next(request)
        return response
