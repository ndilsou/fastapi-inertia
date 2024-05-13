from typing import Annotated, cast

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.testclient import TestClient

from inertia import Inertia, InertiaConfig, InertiaResponse, inertia_dependency_factory

from .utils import get_stripped_html, templates

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
        expected_url = str(client.base_url) + "/"
        expected_head = (
            '<script type="module" src="http://localhost:5173/@vite/client"></script>'
        )
        assert response.text.strip() == get_stripped_html(
            component_name=COMPONENT,
            props=PROPS,
            url=expected_url,
            additional_head_content=expected_head,
        )
