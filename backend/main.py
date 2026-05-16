from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager
import asyncpg

from config import DB_CONNECTION_STRING
from logger import get_logger
from routes import auth, chat, users

logger = get_logger(__name__)
logger.info("Starting application...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Aman application lifecycle...")
    try:
        app.state.pool = await asyncpg.create_pool(dsn=DB_CONNECTION_STRING)
        logger.info("Database connection pool initialized successfully.")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise
    finally:
        if hasattr(app.state, 'pool'):
            await app.state.pool.close()
            logger.info("Database connection pool closed.")

app = FastAPI(
    title="Aman API",
    description="AI Emotional Wellness Support Agent",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)

# ── Health ───────────────────────────────────────────────────────────

@app.get("/")
def home():
    logger.info("Home endpoint accessed.")
    return {"msg": ";3"}
