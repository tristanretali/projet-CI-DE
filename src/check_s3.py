import sys

from botocore.exceptions import BotoCoreError, ClientError

from s3 import BUCKET, ENDPOINT_URL, ensure_bucket, get_client

KEY = "check/hello.txt"
CONTENT = b"hello"


def main():
    client = get_client()
    try:
        ensure_bucket(client)
        client.put_object(Bucket=BUCKET, Key=KEY, Body=CONTENT)
        body = client.get_object(Bucket=BUCKET, Key=KEY)["Body"].read()
        client.delete_object(Bucket=BUCKET, Key=KEY)
    except (BotoCoreError, ClientError) as error:
        sys.exit(f"S3 inaccessible sur {ENDPOINT_URL} : {error}")

    if body != CONTENT:
        sys.exit(f"Contenu relu différent de celui écrit : {body!r}")
    print(f"S3 OK : {ENDPOINT_URL}, bucket '{BUCKET}'")


if __name__ == "__main__":
    main()
