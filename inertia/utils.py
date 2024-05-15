from json import JSONEncoder
from typing import Any, Callable, Literal, Union

from fastapi.encoders import jsonable_encoder
from typing_extensions import NotRequired, TypedDict


class InertiaJsonEncoder(JSONEncoder):
    """
    Custom JSONEncoder to handle Inertia.js response data
    You can extend this class to add custom encoders for your models
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Constructor
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

    def encode(self, value: Any) -> Any:
        """
        Encode the value
        Uses the jsonable_encoder from FastAPI to encode the value
        :param value: Value to encode
        :return: Encoded value
        """
        return jsonable_encoder(value)


class LazyProp:
    """
    Lazy property that can be used to defer the evaluation of a property
    """

    def __init__(self, prop: Union[Callable[[], Any], Any]):
        """
        Constructor
        :param prop: Property to evaluate, can be a callable or a value
        """
        self.prop = prop

    def __call__(self) -> Any:
        """
        Call the property
        :return: Value of the property
        """
        return self.prop() if callable(self.prop) else self.prop


def lazy(prop: Union[Callable[[], Any], Any]) -> LazyProp:
    """
    Create a lazy property
    :param prop: The property to evaluate, can be a callable or a value
    :return: Lazy property
    """
    return LazyProp(prop)


class InertiaContext(TypedDict):
    """
    The jinja template context to pass to render the html for the first request.
    """
    environment: Literal["development", "production"]
    dev_url: str
    is_ssr: bool
    data: str
    css: list[str]
    js: str
    is_react: NotRequired[bool]
    ssr_head: NotRequired[str]
    ssr_body: NotRequired[str]
