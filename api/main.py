import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging.config
import yaml
import asyncio

from api.schemas import AuthRequest, AuthResponse
from api.dependencies import get_captcha_solver, get_auth_service
from services.auth_service import AuthService
from captcha_solver.captcha_api import CaptchaAPI
from config.logging import setup_logging

with open('config/logging.conf', 'r') as f:
    logging_config = yaml.safe_load(f)
    setup_logging(logging_config)

logger = logging.getLogger("app")

app = FastAPI(
    title="Roblox CAPTCHA Bypass API",
    description="REST API для автоматического прохождения Arkose Labs CAPTCHA при авторизации Roblox.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    middleware=[
        Middleware(GZipMiddleware, minimum_size=1000), 
        Middleware(CORSMiddleware, allow_origins=["https://my-frontend.com"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]),
    ],
)

@app.middleware("http")
async def add_exception_handling(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        logger.warning(f"HTTPException: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception as exc:
        logger.exception("Unexpected error occurred")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

async def get_captcha_solver() -> CaptchaAPI:
    return CaptchaAPI(api_key="YOUR_2CAPTCHA_API_KEY")

def get_auth_service(captcha_solver: CaptchaAPI = Depends(get_captcha_solver)) -> AuthService:
    return AuthService(captcha_solver=captcha_solver)

@app.post("/authorize", response_model=AuthResponse, tags=["Authorization"])
async def authorize(request: AuthRequest, auth_service: AuthService = Depends(get_auth_service)):
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")
    
    try:
        user_data = await auth_service.authorize_user(request.username, request.password, request.captcha_token)
        return AuthResponse(status="success", user_id=user_data.user_id, message="Authorized successfully")
    except Exception as e:
        logger.exception("Error during authorization process")
        raise HTTPException(status_code=401, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  
        workers=4,    
        log_level="info",
        timeout_keep_alive=30,
    )
