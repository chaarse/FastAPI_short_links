from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from database import create_tables, delete_tables
from router import router as links_router
from auth import auth_router
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await delete_tables()
    logger.info("База очищена")
    await create_tables()
    logger.info("База готова к работе")
    yield
    logger.info("Выключение")

app = FastAPI(lifespan=lifespan)

app.include_router(links_router)
app.include_router(auth_router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="URL Shortener API",
        version="1.0.0",
        description="API для сокращения ссылок",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi