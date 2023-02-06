from fastapi import APIRouter, Depends, Response, Path, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field

from .store import BaseStore, InMemoryStore, URL_SCHEMA
from .services import UrlService

router = APIRouter()

# TODO move elsewhere
class Url(BaseModel):
    id: str
    original_url: HttpUrl = Field(title="Url to be shortened")

def get_db():
    return InMemoryStore.instance(URL_SCHEMA)

router.post("/urls")
async def create_url(
        url: Url,
        store: BaseStore = Depends(get_db)
):
    url_entity = UrlService(store).create(original_url=url.original_url)

    return Url(url_entity)

router.get("/")
async def read_root():
    return Response("Hello, it's me. Yet another Url Shortener")

router.get("/{short_url}")
async def redirect_url(
        short_url: str = Path(title="Shorthand for the url", default=""),
        store: BaseStore = Depends(get_db)
):
    url_entity = UrlService(store).get(id=short_url)

    if url_entity:
        return RedirectResponse(
            url_entity.original_url,
            status_code=status.HTTP_301_MOVED_PERMANENTLY
        )
    return Response(status_code=status.HTTP_404_NOT_FOUND)