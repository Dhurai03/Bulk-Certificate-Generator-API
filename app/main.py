from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import jobs, certificates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that initializes the SQLite database tables
    when the application starts up.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready backend API for bulk certificate generation. "
        "Accepts bulk recipient lists, generates certificates asynchronously in the background, "
        "tracks real-time job progress, handles individual failures in isolation, and allows PDF retrieval."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(jobs.router, prefix="/api")
app.include_router(certificates.router, prefix="/api")


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint indicating service availability and documentation URL."""
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
    }
