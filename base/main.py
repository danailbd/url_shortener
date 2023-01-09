# import psycopg2
from fastapi import FastAPI, Response, Path
from fastapi.responses import RedirectResponse

from pydantic import BaseModel


class Url(BaseModel):
    original_url: str

db = {}

class UrlModel:
    def generate_url_hash(url):
        # TODO
        pass

    def create(original_url: str):
        # TODO save in db
        # shorthand

app = FastAPI()

@app.get("/")
async def read_root():
    return Response("Hello, it's me. Yet another Url Shortener")

@app.post("/urls")
async def create_url(url: Url):
    

# url_id
@app.get("/{short_url}")
async def redirect_url(
    short_url: str = Path(title="Shorthand for the url")
):
    # TODO
    original_url = "http://dir.bg" # find_by(short_url)
    return RedirectResponse(original_url)