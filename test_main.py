from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from main import app

test_client = TestClient(app=app)


def test_home():
    resp = test_client.get("/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"message": "hello, world!"}


def test_home_with_duplicate_headers():
    resp = test_client.get("/", headers={"x-dummy-header": "foo"})

    assert resp.status_code == HTTPStatus.OK
    assert "dummy_headers" in resp.json()
    assert len(resp.json()["dummy_headers"]) == 1


# data_for_read_items is a fixture from conftest.py
def test_read_items(data_for_read_items):
    resp = test_client.get("/items", params=data_for_read_items)

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["items"]
    assert resp.json()["q"]
    assert resp.json()["q2"]
    assert "q-2" not in resp.json()
    assert "q3" not in resp.json()


def test_read_items_leave_fields_as_default():
    resp = test_client.get("/items", params={})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["items"]
    assert resp.json()["q2"] == ["aa", "bb", "cc"]
    assert "q" not in resp.json()


def test_read_items_with_cookie():
    resp = test_client.get("/items", params={}, cookies={"ads_id": "dummy_cookie"})

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["cookies"]["ads_id"] == "dummy_cookie"


def test_read_items_invalid_query_param():
    resp = test_client.get("/items", params={"q": "az"})

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_read_item():
    resp = test_client.get(
        "/items/1", params={"needy": "abcde"}, headers={"X-Token": "coneofsilence"}
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {
        "item": {
            "id": "1",
            "name": "Foo",
            "description": "There goes my hero",
            "price": 1.00,
        },
        "needy": "abcde",
        "q": None,
        "description": "awesome long description",
    }


def test_read_item_missing_mandatory_query_param():
    resp = test_client.get(
        "/item/1", params={"q": "blahblah"}, headers={"X-Token": "hailhydra"}
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_read_item_invalid_token():
    resp = test_client.get(
        "/items/1", params={"needy": "abcde"}, headers={"X-Token": "hailhydra"}
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json() == {"detail": "Invalid X-Token header"}


def test_read_item_inexistent_item():
    resp = test_client.get(
        "/items/99999", params={"needy": "abcde"}, headers={"X-Token": "coneofsilence"}
    )

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.json() == {"detail": "Item not found"}


def test_create_item():
    resp = test_client.post(
        "/item",
        headers={"X-Token": "coneofsilence"},
        json={
            "id": 3,
            "name": "Bazz",
            "price": 1.590,
            "tax": 0.891,
            "tags": ["i", "j", "k"],
            "images": [{"url": "http://1.2.3.4/img/1.jpg", "name": "test_img"}],
        },
    )

    assert resp.status_code == HTTPStatus.CREATED
    assert resp.json() == {
        "id": 3,
        "name": "Bazz",
        "description": None,
        "price": 1.590,
        "tax": 0.891,
        "price_with_tax": 2.481,
        "tags": ["i", "j", "k"],
        "images": [{"url": "http://1.2.3.4/img/1.jpg", "name": "test_img"}],
    }


def test_create_item_invalid_token():
    resp = test_client.post(
        "/item",
        headers={"X-Token": "hailhydra"},
        json={"id": 3, "name": "Bazz", "price": 1.590},
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json() == {"detail": "Invalid X-Token header"}


def test_create_item_existing_item():
    resp = test_client.post(
        "/item",
        headers={"X-Token": "coneofsilence"},
        json={"id": 2, "name": "Bazz", "price": 1.590},
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json() == {"detail": "Item already exists"}


def test_update_item():
    resp = test_client.put(
        "/item/1",
        params={"q": "blahblah"},
        json={
            "item": {"name": "abc", "price": 0.32},
            "user": {"username": "joe", "full_name": "joe bloggs"},
            "importance": 5,
        },
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["q"] == "blahblah"
    assert resp.json()["importance"] == 5
    assert resp.json()["item"]["price"] == 0.32
    assert resp.json()["user"]["username"] == "joe"


def test_update_item_only_mandatory_fields():
    resp = test_client.put(
        "/item/1",
        json={
            "item": {"name": "abc", "price": 0.32},
            "importance": 5,
        },
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["importance"] == 5
    assert resp.json()["item"]["price"] == 0.32
    assert "user" not in resp.json()
    assert "q" not in resp.json()


def test_update_item_invalid_path():
    resp = test_client.put(
        "/item/0",
        json={
            "item": {"name": "abc", "price": 0.32},
        },
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_update_item_missing_mandatory_body():
    resp = test_client.put(
        "/item/1",
        json={
            "user": {"username": "joe", "full_name": "joe bloggs"},
        },
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_update_item_invalid_body_field():
    resp = test_client.put(
        "/item/1",
        json={
            "item": {"name": "abc", "price": -0.32},
            "user": {"username": "joe", "full_name": "joe bloggs"},
            "importance": 5,
        },
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


@pytest.mark.skipif(False, reason="just playing around")
@pytest.mark.parametrize("name", ["alexnet", "resnet", "lenet"])
def test_get_model(name: str):
    resp = test_client.get(f"/model/{name}")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["model_name"] == name


@pytest.mark.parametrize("name", ["mock_name"])
def test_get_model_invalid_model(name: str):
    resp = test_client.get(f"/model/{name}")

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_create_multiple_images():
    resp = test_client.post(
        "/images/multiple/",
        json=[
            {"url": "http://127.0.0.1/1.png", "name": "img1"},
            {"url": "http://127.0.0.1/2.png", "name": "img2"},
        ],
    )

    assert resp.status_code == HTTPStatus.CREATED
    assert resp.json()[0] == {"url": "http://127.0.0.1/1.png", "name": "img1"}


def test_create_index_weights():
    resp = test_client.post(
        "/index-weights/",
        json={0: "0.5", 1: "1.8", 2: "2.9"},
    )

    assert resp.status_code == HTTPStatus.CREATED
    assert resp.json()["0"] == 0.5
    assert resp.json()["2"] == 2.9


def test_create_index_weights_with_integer_string():
    resp = test_client.post(
        "/index-weights/",
        json={"0": "0.5", "1": "1.8", "2": "2.9"},
    )

    assert resp.status_code == HTTPStatus.CREATED


def test_create_index_weights_with_alphabetic():
    resp = test_client.post(
        "/index-weights/",
        json={"a": "0.5", "b": "1.8", "c": "2.9"},
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_create_event():
    resp = test_client.post(
        "/event/ad6ac861-e46d-46f5-abe9-1aef94155f5b",
        json={
            "start_datetime": "2022-01-01T09:15:27+08:00",
            "end_datetime": "2022-01-31T21:37:58+08:00",
            "repeat_at": "12:09:26",
            "process_after": 180.0,
        },
    )

    assert resp.status_code == HTTPStatus.CREATED
    assert resp.json()["event_id"] == "ad6ac861-e46d-46f5-abe9-1aef94155f5b"
    assert resp.json()["duration"]


def test_create_event_invalid_request():
    resp = test_client.post(
        "/event/123456",
        json={},
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp.json()["detail"]


def test_create_user():
    resp = test_client.post(
        "/user/",
        json={
            "username": "jobbloggs",
            "password": "P@ssw0rd",
            "email": "joe@blogs.com",
            "full_name": "Joe Bloggs",
        },
    )

    assert resp.status_code == HTTPStatus.CREATED
    assert "password" not in resp.json()
    assert "full_name" in resp.json()


def test_create_user_unset_field_excluded():
    resp = test_client.post(
        "/user/",
        json={
            "username": "jobbloggs",
            "password": "P@ssw0rd",
            "email": "joe@blogs.com",
        },
    )

    assert resp.status_code == HTTPStatus.CREATED
    assert resp.json()["full_name"] is None


def test_create_user_malformed():
    resp = test_client.post(
        "/user/",
        json={
            "username": "jobbloggs",
            "email": "joe@blogs.com",
            "dummy": "foo, bar",
        },
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_login():
    resp = test_client.post(
        "/login/", data={"username": "joeblogs", "password": "Passw0rd"}
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["username"] == "joeblogs"
    assert resp.json()["password_hash"] != "Passw0rd"


def test_create_file():
    resp = test_client.post(
        "/file/",
        files=[
            ("file", ("dummy.txt", "hello\nworld\n")),
            ("fileb", ("dummy2.txt", "user\npython\n")),
        ],
        data={"token": "abcdef"},
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["file_size"] == len("hello\nworld\n".encode())
    assert resp.json()["fileb_name"] == "dummy2.txt"
    assert resp.json()["token"] == "abcdef"


def test_create_file_with_no_file():
    resp = test_client.post("/file/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["message"] == "No file sent"


def test_create_files():
    resp = test_client.post(
        "/files/",
        files=[
            ("files", ("dummy1.txt", "hello\nworld\n")),
            ("files", ("dummy2.txt", "use\npython\n")),
        ],
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["file_sizes"] == [
        len("hello\nworld\n".encode()),
        len("use\npython\n".encode()),
    ]


def test_create_upload_file():
    resp = test_client.post(
        "/uploadfile/", files={"file": ("dummy.txt", "hello\nworld\n")}
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["filename"] == "dummy.txt"


def test_create_upload_file_with_no_file():
    resp = test_client.post("/uploadfile/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["message"] == "No upload file sent"


def test_create_upload_files():
    resp = test_client.post(
        "/uploadfiles/",
        files=[
            ("files", ("dummy1.txt", "hello\nworld\n")),
            ("files", ("dummy2.txt", "use\npython\n")),
        ],
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["filenames"] == ["dummy1.txt", "dummy2.txt"]
