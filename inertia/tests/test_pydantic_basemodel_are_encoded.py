import json
from typing import Annotated, cast

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.testclient import TestClient

from inertia import Inertia, InertiaConfig, InertiaResponse, inertia_dependency_factory

from .utils import get_html_soup, templates

app = FastAPI()

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(templates=templates)))
]


class Person(BaseModel):
    name: str
    age: int


PROPS = {
    "person": {
        "name": "John Doe",
        "age": 42,
    },
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    name = PROPS["person"]["name"]
    age = PROPS["person"]["age"]
    return await inertia.render(
        COMPONENT, {"person": Person(name=cast(str, name), age=cast(int, age))}
    )


def test_pydantic_basemodel_are_encoded_on_json_response() -> None:
    with TestClient(app) as client:
        response = client.get("/", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}/",
            "version": "1.0",
        }


def test_pydantic_basemodel_are_encoded_on_html_response() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"

        soup = get_html_soup(response.text)

        script_tag = soup.find(
            "script", {"type": "module", "src": "http://localhost:5173/@vite/client"}
        )
        assert script_tag is not None

        app_div = soup.find("div", {"id": "app"})
        assert app_div is not None
        assert app_div.get("data-page") == json.dumps(
            {
                "component": COMPONENT,
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            }
        )
