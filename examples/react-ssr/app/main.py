from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from inertia import InertiaResponse

from .inertia import InertiaJS, configure_inertia


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        yield {"client": client}


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="dont-look-at-me-im-secret")
configure_inertia(app)


@app.get("/", response_model=None)
async def index(inertia: InertiaJS) -> InertiaResponse:
    return await inertia.render("Index", {"name": "John Doe"})


@app.get("/about", response_model=None)
async def about(inertia: InertiaJS) -> InertiaResponse:
    return await inertia.render("About", {"name": "Bob Doe"})
