import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:8333")
ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "local-access-key")
SECRET_KEY = os.environ.get("S3_SECRET_KEY", "local-secret-key")
BUCKET = os.environ.get("S3_BUCKET", "transactions")


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
