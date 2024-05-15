import json
import os
from typing import Annotated
from unittest.mock import MagicMock, patch

import httpx
from fastapi import Depends, FastAPI
from starlette.testclient import TestClient

from inertia import Inertia, InertiaConfig, InertiaResponse, inertia_dependency_factory

from .utils import get_html_soup, templates

app = FastAPI()
manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")

SSR_URL = "http://some_special_url"
InertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                ssr_enabled=True,
                manifest_json_path=manifest_json,
                ssr_url=SSR_URL,
                templates=templates,
            )
        )
    ),
]
PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


# @patch("requests.post")
@patch.object(httpx.AsyncClient, "post")
def test_calls_inertia_render(post_function: MagicMock) -> None:
    with TestClient(app) as client:
        client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )


RETURNED_JSON = {"head": ["some info in the head"], "body": "some info in the body"}


@patch.object(
    httpx.AsyncClient, "post", return_value=MagicMock(json=lambda: RETURNED_JSON)
)
def test_returns_html(post_function: MagicMock) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_file = manifest["src/main.js"]["css"][0]
    css_file = f"/{css_file}"
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        soup = get_html_soup(response.text)

        script_tag = soup.find("script", {"type": "module", "src": js_file})
        assert script_tag is not None

        css_link_tag = soup.find("link", {"rel": "stylesheet", "href": css_file})
        assert css_link_tag is not None

        for head_item in RETURNED_JSON["head"]:
            assert head_item in soup.find("head").text

        # Check for the presence of the body content
        body_content: str = RETURNED_JSON["body"]
        assert body_content in soup.find("body").text


@patch.object(httpx.AsyncClient, "post", side_effect=Exception())
def test_fallback_to_classic_if_render_errors(post_function: MagicMock) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_file = manifest["src/main.js"]["css"][0]
    css_file = f"/{css_file}"
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"

        soup = get_html_soup(response.text)

        script_tag = soup.find("script", {"type": "module", "src": js_file})
        assert script_tag is not None

        css_link_tag = soup.find("link", {"rel": "stylesheet", "href": css_file})
        assert css_link_tag is not None

        app_div = soup.find("div", {"id": "app"})
        assert app_div is not None

        expected_data_page = {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}/",
            "version": "1.0",
        }
        assert app_div.get("data-page") == json.dumps(expected_data_page)
