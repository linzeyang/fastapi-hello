from decimal import Decimal
from enum import Enum
from http import HTTPStatus
from typing import Dict, List, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Path, Query
from pydantic import BaseModel, Field, HttpUrl

FAKE_SECRET_TOKEN = "coneofsilence"
fake_db = {
    1: {
        "id": "1",
        "name": "Foo",
        "description": "There goes my hero",
        "price": Decimal("1.00"),
    },
    2: {
        "id": "2",
        "name": "Bar",
        "description": "The bartenders",
        "price": Decimal("1.00"),
    },
}


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = Field(None, max_length=100)
    price: Decimal = Field(..., ge=Decimal())
    tax: Optional[Decimal] = None
    tags: List[str] = []
    images: Optional[List[Image]] = None


class User(BaseModel):
    username: str
    full_name: Optional[str] = None


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()


@app.get("/")
def home() -> dict:
    return {"message": "hello, world!"}


@app.get("/items")
def read_items(
    q: Optional[str] = Query(
        None,
        min_length=3,
        max_length=50,
        regex=r"^\w+$",
        title="Query string",
        description="Query string for the items to search",
    ),
    q2: List[str] = Query(["aa", "bb", "cc"], alias="q-2"),
    q3: Optional[str] = Query(None, deprecated=True),
) -> dict:
    results = {
        "items": [
            {"item_id": "Foo"},
            {"item_id": "Bar"},
        ],
    }

    if q:
        results["q"] = q

    results["q2"] = q2

    return results


@app.get("/items/{item_id}")
@app.get("/item/{item_id}")
def read_item(
    item_id: int = Path(..., ge=1, title="The ID of the item"),
    needy: str = Query(...),
    q: Optional[str] = Query(None),
    short: bool = Query(False),
    x_token: str = Header(...),
) -> dict:
    """
    :8000/item/321?needy=whoo&short=1
    :8000/item/321?needy=whoo&short=True
    :8000/item/321?needy=whoo&short=on
    :8000/item/321?needy=whoo&short=yes
    """
    if x_token != FAKE_SECRET_TOKEN:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Invalid X-Token header"
        )

    if item_id not in fake_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item not found")

    return {
        "item": fake_db[item_id],
        "needy": needy,
        "q": q,
        "description": "awesome long description" if not short else "desc",
    }


@app.post("/item")
def create_item(
    item: Item = Body(..., embed=False), x_token: str = Header(...)
) -> dict:
    if x_token != FAKE_SECRET_TOKEN:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Invalid X-Token header"
        )

    if item.id in fake_db:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Item already exists"
        )

    item_dict = item.dict()

    if item.tax:
        item_dict["price_with_tax"] = item.price + item.tax

    return item_dict


@app.put("/item/{item_id}")
def update_item(
    item_id: int = Path(..., ge=1, title="The ID of the item"),
    item: Item = Body(...),
    user: Optional[User] = None,
    importance: int = Body(1, ge=0, le=9),
    q: Optional[str] = None,
) -> dict:
    item_dict = {"id": item_id, "importance": importance, "item": item.dict()}

    if user:
        item_dict["user"] = user.dict()

    if q:
        item_dict["q"] = q

    return item_dict


@app.get("/model/{model_name}")
def get_model(model_name: ModelName) -> dict:
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == ModelName.lenet.value:
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.post("/images/multiple/")
def create_multiple_images(images: List[Image]):
    return images


@app.post("/index-weights/")
def create_index_weights(weights: Dict[int, Decimal]):
    return weights
