from pathlib import Path

from bs4 import BeautifulSoup
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

templates = Jinja2Templates(directory=Path(__file__).parent.absolute() / "templates")


template_dir = Path(__file__).parent.absolute() / "templates"
env = Environment(loader=FileSystemLoader(template_dir))


def get_html_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")

