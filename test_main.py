from http import HTTPStatus

from fastapi.testclient import TestClient

from main import app

test_client = TestClient(app=app)


def test_home():
    resp = test_client.get("/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"message": "hello, world!"}


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
            "tags": ["i", "j", "k"],
            "images": [{"url": "http://1.2.3.4/img/1.jpg", "name": "test_img"}],
        },
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {
        "id": 3,
        "name": "Bazz",
        "description": None,
        "price": 1.590,
        "tax": None,
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
