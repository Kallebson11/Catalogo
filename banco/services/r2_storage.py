import boto3
from django.conf import settings


def obter_cliente_r2():
    return boto3.client(
        "s3",
        endpoint_url=(
            f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        ),
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )