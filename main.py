from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from http import HTTPStatus
from typing import Any, Optional
from uuid import UUID

from fastapi import (
    Body,
    Cookie,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    UploadFile,
)
from pydantic import BaseModel, EmailStr, Field, HttpUrl

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
    url: HttpUrl = Field(..., example="https://example.org/1.png")
    name: str = Field(..., example="A pretty image")


class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = Field(None, max_length=100)
    price: Decimal = Field(..., ge=Decimal())
    tax: Optional[Decimal] = None
    tags: list[str] = []
    images: Optional[list[Image]] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice item",
                "price": Decimal("0.86"),
                "tax": Decimal("0.12"),
                "tags": ["test", "mock"],
                "images": None,
            }
        }


class User(BaseModel):
    username: str = Field(..., example="joebloggs")
    full_name: Optional[str] = Field(None, example="Joe Bloggs")


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserIn(UserBase):
    password: str


class UserOut(UserBase):
    pass


class UserInDB(UserBase):
    hashed_password: str


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()


@app.get("/")
def home(
    x_dummy_header: Optional[list[str]] = Header(default=None, convert_underscores=True)
) -> dict:
    result: dict[str, Any] = {"message": "hello, world!"}

    if x_dummy_header:
        result["dummy_headers"] = x_dummy_header

    return result


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
    q2: list[str] = Query(["aa", "bb", "cc"], alias="q-2"),
    q3: Optional[str] = Query(None, deprecated=True),
    ads_id: Optional[str] = Cookie(None, max_length=128, examples=["70f59c6b"]),
) -> dict:
    results: dict[str, Any] = {
        "items": [
            {"item_id": "Foo"},
            {"item_id": "Bar"},
        ],
    }

    if q:
        results["q"] = q

    results["q2"] = q2

    if ads_id:
        results["cookies"] = {"ads_id": ads_id}

    return results


@app.get("/items/{item_id}")
@app.get("/item/{item_id}")
def read_item(
    item_id: int = Path(..., ge=1, title="The ID of the item"),
    needy: str = Query(...),
    q: Optional[str] = Query(None),
    short: bool = Query(False),
    x_token: str = Header(..., convert_underscores=True),
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


@app.post("/item", status_code=HTTPStatus.CREATED)
def create_item(
    item: Item = Body(
        ...,
        embed=False,
        examples=[
            {
                "summary": "A normal example",
                "description": "normally do this",
                "value": {
                    "name": "Foo",
                    "description": "A very nice item",
                    "price": Decimal("0.86"),
                    "tax": Decimal("0.12"),
                },
            },
            {
                "summary": "An invalid example",
                "description": "this is invalid",
                "value": {
                    "name": 123,
                    "description": "A very nice item",
                    "tax": Decimal("0.12"),
                },
            },
        ],
    ),
    x_token: str = Header(...),
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
    item: Item = Body(
        ...,
        examples=[
            {
                "name": "Foo",
                "description": "A very nice item",
                "price": Decimal("0.86"),
                "tax": Decimal("0.12"),
                "tags": ["test", "mock"],
                "images": None,
            }
        ],
    ),
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


@app.get("/model/{model_name}", response_model=dict[str, str])
def get_model(model_name: ModelName) -> dict:
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == ModelName.lenet.value:
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.post(
    "/images/multiple/", response_model=list[Image], status_code=HTTPStatus.CREATED
)
def create_multiple_images(images: list[Image]):
    return images


@app.post(
    "/index-weights/", response_model=dict[int, Decimal], status_code=HTTPStatus.CREATED
)
def create_index_weights(weights: dict[int, Decimal]):
    return weights


@app.post(
    "/event/{event_id}", response_model=dict[str, Any], status_code=HTTPStatus.CREATED
)
def create_event(
    event_id: UUID,
    start_datetime: Optional[datetime] = Body(None),
    end_datetime: Optional[datetime] = Body(None),
    repeat_at: Optional[time] = Body(None),
    process_after: Optional[timedelta] = Body(None),
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process

    return {
        "event_id": event_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "repeat_at": repeat_at,
        "process_after": process_after,
        "duration": duration,
    }


def fake_password_hasher(raw_password: str) -> str:
    return "supersecret" + raw_password


def fake_save_user(user_in: UserIn) -> UserInDB:
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDB(**user_in.dict(), hashed_password=hashed_password)
    return user_in_db


@app.post(
    "/user/",
    response_model=UserOut,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.CREATED,
)
def create_user(user: UserIn):
    return fake_save_user(user_in=user)


@app.post("/login/")
def login(username: str = Form(), password: str = Form()):
    return {"username": username, "password_hash": hash(password)}


@app.post("/file/")
async def create_file(
    file: Optional[bytes] = File(default=None, description="A file read as bytes"),
    fileb: Optional[UploadFile] = File(default=None),
    token: Optional[str] = Form(default=None),
):
    if not file:
        return {"message": "No file sent"}

    return {
        "file_size": len(file),
        "fileb_name": fileb.filename if fileb else None,
        "token": token,
    }


@app.post("/files/")
async def create_files(
    files: list[bytes] = File(description="Multiple files as bytes"),
):
    return {"file_sizes": [len(file) for file in files]}


@app.post("/uploadfile/")
async def create_upload_file(
    file: Optional[UploadFile] = File(
        default=None, description="A file read as UploadFile"
    )
):
    if not file:
        return {"message": "No upload file sent"}

    return {"filename": file.filename}


@app.post("/uploadfiles/")
async def create_upload_files(
    files: list[UploadFile] = File(description="Multiple files as UploadFile"),
):
    return {"filenames": [file.filename for file in files]}
