"""FastAPI application main entry point."""
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, msf

# Create FastAPI application instance
app = FastAPI(
    title="C2协同工具API",
    description="C2协同工具后端API - Metasploit集成",
    version="1.0.0",
    debug=True
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    健康检查接口，用于前端检测后端服务是否存活
    """
    return {
        "status": "ok",
        "message": "backend is running",
        "timestamp": str(datetime.now())
    }

# Register routers
app.include_router(auth.router)
app.include_router(msf.router)


@app.get("/")
async def root():
    """Root endpoint returning API status message."""
    return {"message": "C2协同工具API运行中"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
