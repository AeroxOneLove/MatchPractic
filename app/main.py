from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.routers import routers


def create_app():
    app = FastAPI(debug=config.DEBUG)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routers)

    return app
