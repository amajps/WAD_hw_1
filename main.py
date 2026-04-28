from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from config import settings
from routers.auth import router as auth_router
from routers.github_oauth import router as github_router
from routers.chat import router as chat_router
import redis_client

app = FastAPI(title="HW1 LLM Chat API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    redis_client.redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client.redis_client is not None:
        await redis_client.redis_client.close()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"})

app.include_router(auth_router)
app.include_router(github_router)
app.include_router(chat_router)
