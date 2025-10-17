"""FastAPIメインアプリケーション"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from app.core.config import settings
from app.api.v1 import tasks
from app.db.database import init_db

app = FastAPI(
    title="AI見積りシステム API",
    description="AI見積りシステムのバックエンドAPI",
    version="0.1.0",
)

# CORS設定
cors_origins = (
    [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if isinstance(settings.CORS_ORIGINS, str)
    else settings.CORS_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    # データベース初期化
    init_db()
    # アップロードディレクトリ作成
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {
        "message": "AI見積りシステム API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ルーター登録
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}", tags=["tasks"])

# UI (静的ファイル) 提供
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")
