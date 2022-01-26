from decimal import Decimal
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    tax: Optional[Decimal] = None


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
    item_id: int, needy: str, q: Optional[str] = None, short: bool = False
) -> dict:
    """
    :8000/item/321?needy=whoo&short=1
    :8000/item/321?needy=whoo&short=True
    :8000/item/321?needy=whoo&short=on
    :8000/item/321?needy=whoo&short=yes
    """
    return {
        "item_id": item_id,
        "needy": needy,
        "q": q,
        "description": "awesome long description" if not short else "desc",
    }


@app.post("/item")
def create_item(item: Item) -> dict:
    item_dict = item.dict()

    if item.tax:
        item_dict["price_with_tax"] = item.price + item.tax

    return item_dict


@app.put("/item/{item_id}")
def update_item(item_id: int, item: Item, q: Optional[str] = None) -> dict:
    item_dict = item.dict()
    item_dict["id"] = item_id

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
