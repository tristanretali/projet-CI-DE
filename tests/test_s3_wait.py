import time

import pytest
from botocore.exceptions import ClientError, ConnectionClosedError

from s3 import wait_for_s3


class FakeClient:
    def __init__(self, errors):
        self.errors = list(errors)
        self.calls = 0

    def head_bucket(self, Bucket):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)


def connection_closed():
    return ConnectionClosedError(endpoint_url="http://localhost:8333")


def client_error(status):
    return ClientError(
        {"Error": {"Code": str(status)}, "ResponseMetadata": {"HTTPStatusCode": status}},
        "HeadBucket",
    )


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


def test_waits_while_the_service_closes_connections():
    client = FakeClient([connection_closed(), connection_closed()])

    wait_for_s3(client, "transactions")

    assert client.calls == 3


def test_waits_while_the_service_answers_with_a_server_error():
    client = FakeClient([client_error(503)])

    wait_for_s3(client, "transactions")

    assert client.calls == 2


def test_does_not_wait_on_client_error():
    client = FakeClient([client_error(403)])

    with pytest.raises(ClientError):
        wait_for_s3(client, "transactions")

    assert client.calls == 1


def test_gives_up_after_the_timeout():
    client = FakeClient([connection_closed()] * 5)

    with pytest.raises(ConnectionClosedError):
        wait_for_s3(client, "transactions", timeout=0)

    assert client.calls == 1
