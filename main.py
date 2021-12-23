from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home() -> dict:
    return {"message": "hello, world!"}


@app.get("/item/{item_id}")
def read_item(item_id: int, q: Optional[str] = None) -> dict:
    return {"item_id": item_id, "q": q}
