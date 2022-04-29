from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from main import app

test_client = TestClient(app=app)


def test_home():
    resp = test_client.get("/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"message": "hello, world!"}


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
