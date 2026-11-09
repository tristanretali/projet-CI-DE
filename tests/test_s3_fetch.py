import time

import pytest
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    IncompleteReadError,
)

from s3 import fetch_csv_files

KEY_1 = "incoming/transactions_001.csv"
KEY_2 = "incoming/transactions_002.csv"


class FakeBody:
    def __init__(self, content, error=None):
        self.content = content
        self.error = error

    def read(self):
        if self.error:
            raise self.error
        return self.content


class FakePaginator:
    def __init__(self, client):
        self.client = client

    def paginate(self, Bucket, Prefix):
        self.client.list_calls += 1
        if self.client.list_errors:
            raise self.client.list_errors.pop(0)
        yield {"Contents": [{"Key": key} for key in self.client.objects]}


class FakeClient:
    def __init__(self, objects, get_errors=None, list_errors=None, read_errors=None):
        self.objects = objects
        self.get_errors = {key: list(errs) for key, errs in (get_errors or {}).items()}
        self.read_errors = {
            key: list(errs) for key, errs in (read_errors or {}).items()
        }
        self.list_errors = list(list_errors or [])
        self.list_calls = 0
        self.get_calls = {key: 0 for key in objects}

    def get_paginator(self, name):
        return FakePaginator(self)

    def get_object(self, Bucket, Key):
        self.get_calls[Key] += 1
        errors = self.get_errors.get(Key)
        if errors:
            raise errors.pop(0)
        read_errors = self.read_errors.get(Key)
        error = read_errors.pop(0) if read_errors else None
        return {"Body": FakeBody(self.objects[Key], error)}


def connection_closed():
    return ConnectionClosedError(endpoint_url="http://localhost:8333")


def client_error(status, code="Error"):
    return ClientError(
        {"Error": {"Code": code}, "ResponseMetadata": {"HTTPStatusCode": status}},
        "GetObject",
    )


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


OBJECTS = {KEY_1: b"un", KEY_2: b"deux"}


def test_download_is_retried_after_a_network_error():
    client = FakeClient(OBJECTS, get_errors={KEY_1: [connection_closed()] * 2})

    contents = fetch_csv_files(client, "transactions")

    assert contents == OBJECTS
    assert client.get_calls == {KEY_1: 3, KEY_2: 1}


def test_download_is_retried_after_a_server_error():
    client = FakeClient(OBJECTS, get_errors={KEY_2: [client_error(503)]})

    assert fetch_csv_files(client, "transactions") == OBJECTS
    assert client.get_calls[KEY_2] == 2


def test_truncated_download_is_retried():
    truncated = IncompleteReadError(actual_bytes=1, expected_bytes=2)
    client = FakeClient(OBJECTS, read_errors={KEY_1: [truncated]})

    assert fetch_csv_files(client, "transactions") == OBJECTS
    assert client.get_calls[KEY_1] == 2


def test_listing_is_retried():
    client = FakeClient(OBJECTS, list_errors=[connection_closed()])

    assert fetch_csv_files(client, "transactions") == OBJECTS
    assert client.list_calls == 2


def test_gives_up_after_three_attempts():
    client = FakeClient(OBJECTS, get_errors={KEY_1: [connection_closed()] * 5})

    with pytest.raises(ConnectionClosedError):
        fetch_csv_files(client, "transactions")

    assert client.get_calls[KEY_1] == 3


def test_missing_file_is_not_retried():
    client = FakeClient(OBJECTS, get_errors={KEY_1: [client_error(404, "NoSuchKey")]})

    with pytest.raises(ClientError):
        fetch_csv_files(client, "transactions")

    assert client.get_calls[KEY_1] == 1


def test_access_denied_is_not_retried():
    denied = client_error(403, "AccessDenied")
    client = FakeClient(OBJECTS, get_errors={KEY_1: [denied]})

    with pytest.raises(ClientError):
        fetch_csv_files(client, "transactions")

    assert client.get_calls[KEY_1] == 1
