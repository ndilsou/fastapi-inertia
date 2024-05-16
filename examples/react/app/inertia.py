from pathlib import Path
from fastapi import Depends, FastAPI
from typing import Annotated
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from inertia import (
    InertiaConfig,
    InertiaVersionConflictException,
    inertia_dependency_factory,
    Inertia,
    inertia_request_validation_exception_handler,
    inertia_version_conflict_exception_handler,
)

BASE_DIR = Path(__file__).resolve().parent.parent
UI_ASSETS_PREFIX = "/ui"
templates = Jinja2Templates(directory=BASE_DIR / "app/templates")

inertia_config = InertiaConfig(
    templates=templates,
    entrypoint_filename="main.tsx",
    assets_prefix=UI_ASSETS_PREFIX,
    is_react=True,
    use_flash_messages=True,
    root_directory="ui",
    environment="production",
)

inertia_dependency = inertia_dependency_factory(inertia_config)

InertiaJS = Annotated[Inertia, Depends(inertia_dependency)]


def configure_inertia(app: FastAPI) -> None:
    app.add_exception_handler(
        InertiaVersionConflictException, inertia_version_conflict_exception_handler
    )
    app.add_exception_handler(
        RequestValidationError, inertia_request_validation_exception_handler
    )

    if inertia_config.environment == "production":
        webapp_dir = BASE_DIR / "dist"
        app.mount(
            UI_ASSETS_PREFIX,
            StaticFiles(directory=webapp_dir),
            name="ui_assets",
        )
