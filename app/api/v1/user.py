from fastapi import APIRouter

router = APIRouter(prefix="/v1/user", tags=["user"])


@router.post("/register")
async def register():
    return {"message": "register endpoint"}


@router.post("/login")
async def login():
    return {"message": "login endpoint"}


@router.get("/profile")
async def profile():
    return {"message": "profile endpoint"}


@router.get("/balance")
async def balance():
    return {"balance": 0.0}


@router.get("/api-keys")
async def list_api_keys():
    return {"data": []}


@router.post("/api-keys")
async def create_api_key():
    return {"message": "api key created"}
