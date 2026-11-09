import os
import time

import boto3
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    HTTPClientError,
    IncompleteReadError,
)

from retry import retry

ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:8333")
ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "local-access-key")
SECRET_KEY = os.environ.get("S3_SECRET_KEY", "local-secret-key")
BUCKET = os.environ.get("S3_BUCKET", "transactions")
INCOMING_PREFIX = "incoming/"


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="us-east-1",
        config=Config(
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def ensure_bucket(client, bucket=BUCKET):
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as error:
        if error.response["Error"]["Code"] not in ("404", "NoSuchBucket", "NotFound"):
            raise
        client.create_bucket(Bucket=bucket)


def is_transient(error):
    if isinstance(error, ClientError):
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
        return status >= 500
    return isinstance(error, (HTTPClientError, IncompleteReadError))


def wait_for_s3(client, bucket=BUCKET, timeout=60):
    deadline = time.monotonic() + timeout
    while True:
        try:
            ensure_bucket(client, bucket)
            return
        except (BotoCoreError, ClientError) as error:
            if not is_transient(error) or time.monotonic() >= deadline:
                raise
            time.sleep(1)


@retry(exceptions=(BotoCoreError, ClientError), retry_if=is_transient)
def list_csv_keys(client, bucket):
    keys = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=INCOMING_PREFIX):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    return [key for key in keys if key.endswith(".csv")]


@retry(exceptions=(BotoCoreError, ClientError), retry_if=is_transient)
def read_object(client, bucket, key):
    return client.get_object(Bucket=bucket, Key=key)["Body"].read()


def fetch_csv_files(client, bucket=BUCKET):
    return {
        key: read_object(client, bucket, key)
        for key in list_csv_keys(client, bucket)
    }
