from dataclasses import dataclass
from json import JSONEncoder
from typing import Literal, Type

from fastapi.templating import Jinja2Templates

from .utils import InertiaJsonEncoder


@dataclass
class InertiaConfig:
    """
    Configuration class for Inertia

    Attributes:
        templates (Jinja2Templates): The Jinja2Templates instance to use for rendering the HTML
        environment (Literal["development", "production"]): The environment the application is running in
        version (str): The version of Inertia.js to use
        json_encoder (Type[JSONEncoder]): The JSONEncoder to use for encoding the data
        manifest_json_path (str): The path to the manifest.json file
        root_directory (str): The root directory of the project
        root_template_filename (str): The name of the root template file
        entrypoint_filename (str): The name of the entrypoint file
        dev_url (str): The URL of the Vite development server
        ssr_url (str): The URL of the Vite SSR server
        ssr_enabled (bool): Whether SSR is enabled
        is_react (bool): Whether the project uses React. This is used to inject the React refresh runtime into the page in development mode.
        use_flash_messages (bool): Whether to use flash messages
        use_flash_errors (bool): Whether to use flash errors
        flash_message_key (str): The key to use for flash messages
        flash_error_key (str): The key to use for flash errors
    """

    templates: Jinja2Templates
    environment: Literal["development", "production"] = "development"
    version: str = "1.0"
    json_encoder: Type[JSONEncoder] = InertiaJsonEncoder
    manifest_json_path: str = "dist/.vite/manifest.json"
    root_directory: str = "src"
    root_template_filename: str = "index.html"
    entrypoint_filename: str = "main.js"
    dev_url: str = "http://localhost:5173"
    ssr_url: str = "http://localhost:13714"
    ssr_enabled: bool = False
    is_react: bool = False
    use_flash_messages: bool = False
    use_flash_errors: bool = False
    flash_message_key: str = "messages"
    flash_error_key: str = "errors"
