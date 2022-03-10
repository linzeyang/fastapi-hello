import pytest
import requests


@pytest.fixture
def data_for_read_items():
    return {
        "q": "abcdefg",
        "q-2": ["1", "2", "3"],
        "q3": "im deprecated",
    }


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise RuntimeError("Network access not allowed during testing!")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())
