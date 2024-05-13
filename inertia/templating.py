from typing import Literal, Union
from typing_extensions import TypedDict, NotRequired
from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.runtime import Context
from markupsafe import Markup


class InertiaContext(TypedDict):
    environment: Literal["development", "production"]
    dev_url: str
    is_ssr: bool
    is_react: NotRequired[bool]
    data: str
    ssr_head: NotRequired[str]
    ssr_body: NotRequired[str]
    css: list[str]
    js: str


class InertiaExtension(Extension):
    tags = set(["inertia_head", "inertia_body"])

    def parse(self, parser):
        tag_name = next(parser.stream).value
        lineno = parser.stream.current.lineno
        ctx_ref = nodes.ContextReference()

        node = self.call_method(f"_render_{tag_name}", [ctx_ref], lineno=lineno)
        return nodes.Output([node]).set_lineno(lineno)

    def _render_inertia_head(self, context: Context):
        fragments: list[str] = []
        inertia: InertiaContext = context["inertia"]

        if inertia["environment"] == "development":
            fragments.append(
                _vite_dev_head(
                    inertia["dev_url"],
                    inertia.get("is_react", False),
                )
            )

        if inertia.get("is_ssr", False):
            fragments.append(inertia["ssr_head"])

        if inertia["css"]:
            for css_file in inertia["css"]:
                fragments.append(f'<link rel="stylesheet" href="{css_file}">')

        return Markup("\n".join(fragments))

    def _render_inertia_body(self, context: Context):
        fragments: list[str] = []
        inertia: InertiaContext = context["inertia"]
        if inertia["is_ssr"]:
            fragments.append(inertia["ssr_body"])
        else:
            fragments.append(f"<div id=\"app\" data-page='{inertia['data']}'></div>")

        fragments.append(f'<script type="module" src="{inertia["js"]}"></script>')
        return Markup("\n".join(fragments))


def _vite_dev_head(dev_url: str, is_react: bool = False):
    fragments = []
    if is_react:
        fragments.append(f"""\
        <script type="module">
          import RefreshRuntime from '{dev_url}/@react-refresh'
          RefreshRuntime.injectIntoGlobalHook(window)
          window.$RefreshReg$ = () => {{}}
          window.$RefreshSig$ = () => (type) => type
          window.__vite_plugin_react_preamble_installed__ = true
        </script>
        """)

    fragments.append(f'<script type="module" src="{dev_url}/@vite/client"></script>')
    return Markup("\n".join(fragments))
