import json
import os
from typing import Annotated

from fastapi import Depends, FastAPI
from starlette.testclient import TestClient

from inertia import Inertia, InertiaConfig, InertiaResponse, inertia_dependency_factory

from .utils import get_html_soup, templates

app = FastAPI()
manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")

PREFIX = "custom-prefix"
InertiaDepWithPrefix = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                templates=templates,
                manifest_json_path=manifest_json,
                assets_prefix=PREFIX,
                environment="production",
            )
        )
    ),
]

InertiaDepWithoutPrefix = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                templates=templates,
                manifest_json_path=manifest_json,
                environment="production",
            )
        )
    ),
]


PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/with-prefix", response_model=None)
async def with_prefix(inertia: InertiaDepWithPrefix) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)

@app.get("/without-prefix", response_model=None)
async def without_prefix(inertia: InertiaDepWithoutPrefix) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_production_assets_has_custom_prefix() -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_file = manifest["src/main.js"]["css"][0]
    css_file = f"/{PREFIX}/{css_file}"
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{PREFIX}/{js_file}"
    with TestClient(app) as client:
        response = client.get("/with-prefix")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"

        soup = get_html_soup(response.text)

        # Check for the presence of the main script tag
        script_tag = soup.find("script", {"type": "module", "src": js_file})
        assert script_tag is not None

        # Check for the presence of the CSS link tag
        css_link_tag = soup.find("link", {"rel": "stylesheet", "href": css_file})
        assert css_link_tag is not None

def test_production_assets_has_default_prefix() -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_file = manifest["src/main.js"]["css"][0]
    css_file = f"/{css_file}"
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/without-prefix")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"

        soup = get_html_soup(response.text)

        # Check for the presence of the main script tag
        script_tag = soup.find("script", {"type": "module", "src": js_file})
        assert script_tag is not None

        # Check for the presence of the CSS link tag
        css_link_tag = soup.find("link", {"rel": "stylesheet", "href": css_file})
        assert css_link_tag is not None