import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api import webhooks, feedback, repos
from app.core.telemetry import setup_telemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

setup_telemetry("codesentinel-api")

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("codesentinel_starting", version="0.1.0")
    yield
    logger.info("codesentinel_shutting_down")


app = FastAPI(
    title="CodeSentinel API",
    description="LLM-powered automated code review assistant",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(repos.router, prefix="/repos", tags=["Repositories"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
