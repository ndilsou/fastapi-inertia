import asyncio
import atexit
import json
import logging
import posixpath
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, TypedDict, TypeVar, Union, cast

from fastapi import Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from starlette.responses import RedirectResponse
from typing_extensions import NotRequired

from .config import InertiaConfig
from .exceptions import InertiaVersionConflictException
from .templating import InertiaExtension
from .utils import InertiaContext, LazyProp

try:
    from httpx import AsyncClient
except ModuleNotFoundError:
    pass

logger = logging.getLogger(__name__)

InertiaResponse = Union[HTMLResponse, JSONResponse]

T = TypeVar("T")


class FlashMessage(TypedDict):
    """
    Flash message type
    """

    message: str
    category: str


class Inertia:
    """
    Inertia class to handle Inertia.js responses
    To be used as a dependency in FastAPI
    You should use the `inertia_dependency_factory` function to create a dependency, in order
    to pass the configuration to the Inertia class
    """

    @dataclass
    class InertiaFiles:
        """
        Helper class to store the CSS and JS files for Inertia.js
        """

        css_files: list[str]
        js_file: str

    _request: Request
    _config: InertiaConfig
    _component: str
    _props: dict[str, Any]
    _inertia_files: InertiaFiles

    def __init__(self, request: Request, config_: InertiaConfig) -> None:
        """
        Constructor
        :param request: FastAPI Request object
        :param config_: InertiaConfig object
        """
        self._request = request
        self._component = ""
        self._props = {}
        self._config = config_
        self._http_client = None
        self._set_inertia_files()

        if self._is_stale:
            raise InertiaVersionConflictException(url=str(request.url))

    @property
    def _partial_keys(self) -> list[str]:
        """
        Get the keys of the partial data
        :return: List of keys
        """
        return self._request.headers.get("X-Inertia-Partial-Data", "").split(",")

    @property
    def _is_inertia_request(self) -> bool:
        """
        Check if the request is an Inertia request (requesting JSON)
        :return: True if the request is an Inertia request, False otherwise
        """
        return "X-Inertia" in self._request.headers

    @property
    def _is_stale(self) -> bool:
        """
        Check if the Inertia request is stale (different from the current version)
        :return: True if the version is stale, False otherwise
        """
        return bool(
            self._request.headers.get("X-Inertia-Version", self._config.version)
            != self._config.version
        )

    @property
    def _is_a_partial_render(self) -> bool:
        """
        Check if the request is a partial render
        :return: True if the request is a partial render, False otherwise
        """
        return (
            "X-Inertia-Partial-Data" in self._request.headers
            and self._request.headers.get("X-Inertia-Partial-Component", "")
            == self._component
        )

    def _get_page_data(self) -> Dict[str, Any]:
        """
        Get the data for the page
        :return: A dictionary with the page data
        """
        return {
            "component": self._component,
            "props": self._build_props(),
            "url": str(self._request.url),
            "version": self._config.version,
        }

    def _get_flashed_messages(self) -> list[FlashMessage]:
        """
        Get the flashed messages from the session (pop them from the session)
        :return: List of flashed messages
        """
        return (
            cast(list[FlashMessage], self._request.session.pop("_messages"))
            if "_messages" in self._request.session
            else []
        )

    def _get_flashed_errors(self) -> dict[str, str]:
        """
        Get the flashed errors from the session (pop them from the session)
        :return: Dict of flashed errors
        """
        return (
            cast(dict[str, str], self._request.session.pop("_errors"))
            if "_errors" in self._request.session
            else {}
        )

    def _set_inertia_files(self) -> None:
        """
        Set the Inertia files (CSS and JS) based on the configuration
        """
        if self._config.environment == "production" or self._config.ssr_enabled:
            manifest = _read_manifest_file(self._config.manifest_json_path)

            asset_manifest = manifest[
                f"{self._config.root_directory}/{self._config.entrypoint_filename}"
            ]

            css_files = asset_manifest.get("css", [])
            js_file = asset_manifest["file"]

            prefix = self._config.assets_prefix or ""
            self._inertia_files = self.InertiaFiles(
                css_files=[
                    posixpath.join("/", prefix, css_file) for css_file in css_files
                ],
                js_file=posixpath.join("/", prefix, js_file),
            )
        else:
            js_file = f"{self._config.dev_url}/{self._config.root_directory}/{self._config.entrypoint_filename}"
            self._inertia_files = self.InertiaFiles(css_files=[], js_file=js_file)

    @classmethod
    def _deep_transform_callables(
        cls, prop: Union[Callable[..., Any], Dict[str, Any], BaseModel, Any]
    ) -> Any:
        """
        Deeply transform callables in a dictionary, evaluating them if they are callables
        If the value is a BaseModel, it will call the model_dump method.
        Recursive function

        :param prop: Property to transform
        :return: Transformed property
        """
        if not isinstance(prop, dict):
            if callable(prop):
                return prop()
            if isinstance(prop, BaseModel):
                return prop.model_dump()
            return prop

        prop_ = prop.copy()
        for key in list(prop_.keys()):
            prop_[key] = cls._deep_transform_callables(prop_[key])

        return prop_

    def _build_props(self) -> Union[Dict[str, Any], Any]:
        """
        Build the props for the page.
        If the request is a partial render, it will only include the partial keys
        :return: A dictionary with the props
        """
        _props = self._props.copy()

        for key in list(_props.keys()):
            if self._is_a_partial_render:
                if key not in self._partial_keys:
                    del _props[key]
            else:
                if isinstance(_props[key], LazyProp):
                    del _props[key]

        return self._deep_transform_callables(_props)

    async def _render_ssr(self) -> HTMLResponse:
        """
        Render the page using SSR, calling the Inertia SSR server.
        :return: The HTML response
        """

        client = _get_or_create_httpx_client()

        data = json.dumps(self._get_page_data(), cls=self._config.json_encoder)
        response = await client.post(
            f"{self._config.ssr_url}/render",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        response_json = response.json()

        head = response_json["head"]
        displayable_head = "\n".join(head)
        body = response_json["body"]

        return self._config.templates.TemplateResponse(
            name=self._config.root_template_filename,
            request=self._request,
            context={
                "inertia": InertiaContext(
                    environment=self._config.environment,
                    is_react=self._config.is_react,
                    dev_url=self._config.dev_url,
                    is_ssr=True,
                    ssr_head=displayable_head,
                    ssr_body=body,
                    js=self._inertia_files.js_file,
                    css=self._inertia_files.css_files,
                ),
            },
        )

    def share(self, **props: Any) -> None:
        """
        Share props between functions. Useful to share props between dependencies/middlewares and routes
        :param props: Props to share
        """
        self._props.update(props)

    def flash(self, message: str, category: str) -> None:
        """
        Flash a message to the session
        If flash messages are not enabled, it will raise a NotImplementedError
        :param message: message to flash
        :param category: category of the message
        """
        if not self._config.use_flash_messages:
            raise NotImplementedError("Flash messages are not enabled")

        if "_messages" not in self._request.session:
            self._request.session["_messages"] = []

        message_: FlashMessage = {"message": message, "category": category}
        self._request.session["_messages"].append(message_)

    @staticmethod
    def location(url: str) -> Response:
        """
        Return a response with a location header.
        Useful to redirect to a different page (outside of this server)
        :param url: URL to redirect to
        :return: Response
        """
        return Response(
            status_code=status.HTTP_409_CONFLICT,
            headers={"X-Inertia-Location": url},
        )

    def back(self) -> RedirectResponse:
        """
        Redirect back to the previous page
        :return: RedirectResponse
        """
        status_code = (
            status.HTTP_307_TEMPORARY_REDIRECT
            if self._request.method == "GET"
            else status.HTTP_303_SEE_OTHER
        )
        return RedirectResponse(
            url=self._request.headers["Referer"], status_code=status_code
        )

    async def render(
        self, component: str, props: Optional[Dict[str, Any]] = None
    ) -> InertiaResponse:
        """
        Render the page
        If the request is an Inertia request, it will return a JSONResponse
        If SSR is enabled, it will try to render the page using SSR.
        If an error occurs, it will fall back to server-side template rendering
        :param component: The component name to render
        :param props: The props to pass to the component
        :return: HTMLResponse or JSONResponse
        """
        if self._config.use_flash_messages:
            self._props.update(
                {self._config.flash_message_key: self._get_flashed_messages()}
            )

        if self._config.use_flash_errors:
            self._props.update(
                {self._config.flash_error_key: self._get_flashed_errors()}
            )

        self._component = component
        self._props.update(props or {})

        if "X-Inertia" in self._request.headers:
            return JSONResponse(
                content=self._get_page_data(),
                headers={
                    "Vary": "Accept",
                    "X-Inertia": "true",
                },
            )

        if self._config.ssr_enabled:
            try:
                return await self._render_ssr()
            except Exception as exc:
                logger.error(
                    f"An error occurred in rendering SSR (falling back to classic rendering): {exc}"
                )

        # Fallback to server-side template rendering
        page_json = json.dumps(
            json.dumps(self._get_page_data(), cls=self._config.json_encoder)
        )

        return self._config.templates.TemplateResponse(
            name=self._config.root_template_filename,
            request=self._request,
            context={
                "inertia": InertiaContext(
                    environment=self._config.environment,
                    is_react=self._config.is_react,
                    dev_url=self._config.dev_url,
                    is_ssr=False,
                    data=page_json,
                    js=self._inertia_files.js_file,
                    css=self._inertia_files.css_files,
                ),
            },
        )


def inertia_dependency_factory(config_: InertiaConfig) -> Callable[[Request], Inertia]:
    """
    Create a dependency for Inertia, passing the configuration
    :param config_: InertiaConfig object
    :return: Dependency
    """

    config_.templates.env.add_extension(InertiaExtension)

    def inertia_dependency(request: Request) -> Inertia:
        """
        Dependency for Inertia
        :param request: FastAPI Request object
        :return: Inertia object
        """
        return Inertia(request, config_)

    return inertia_dependency


class ViteManifestChunk(TypedDict):
    file: str
    src: NotRequired[str]
    isEntry: NotRequired[bool]
    isDynamicEntry: NotRequired[bool]
    dynamicImports: NotRequired[list[str]]
    css: NotRequired[list[str]]
    assets: NotRequired[list[str]]
    imports: NotRequired[list[str]]


ViteManifest = Dict[str, ViteManifestChunk]


@lru_cache
def _read_manifest_file(path: str) -> ViteManifest:
    with open(path, "r") as manifest_file:
        return cast(ViteManifest, json.load(manifest_file))


_ASYNC_HTTPX_CLIENT: Optional["AsyncClient"] = None


def _get_or_create_httpx_client() -> "AsyncClient":
    """
    Get or create the httpx async client
    :return: The httpx client
    """

    global _ASYNC_HTTPX_CLIENT

    if _ASYNC_HTTPX_CLIENT is None:
        _ASYNC_HTTPX_CLIENT = AsyncClient()

        def close_httpx_client() -> None:
            # We need to find a way to close the client when the app is shutting down
            if _ASYNC_HTTPX_CLIENT is not None:
                try:
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(_ASYNC_HTTPX_CLIENT.aclose())
                except RuntimeError:
                    logger.debug("the event loop is already closed")
                except Exception as exc:
                    logger.warning(
                        f"An error occurred while closing the httpx client: {exc}"
                    )

        atexit.register(close_httpx_client)

    return _ASYNC_HTTPX_CLIENT
