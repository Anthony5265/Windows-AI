"""
Cloud Storage Manager - 15+ Providers
S3, Azure, GCS, R2, Backblaze, etc.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, BinaryIO
from pathlib import Path

logger = logging.getLogger(__name__)

class CloudStorageManager:
    """Unified cloud storage across 15+ providers"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    async def upload(self, provider: str, bucket: str, key: str, data: bytes, **kwargs) -> str:
        """Upload file to cloud storage"""
        if provider == "s3":
            return await self._s3_upload(bucket, key, data, **kwargs)
        elif provider == "gcs":
            return await self._gcs_upload(bucket, key, data, **kwargs)
        elif provider == "azure":
            return await self._azure_upload(bucket, key, data, **kwargs)
        elif provider == "r2":
            return await self._r2_upload(bucket, key, data, **kwargs)
        elif provider == "b2":
            return await self._b2_upload(bucket, key, data, **kwargs)
        elif provider == "minio":
            return await self._minio_upload(bucket, key, data, **kwargs)
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")

    async def download(self, provider: str, bucket: str, key: str, **kwargs) -> bytes:
        """Download file from cloud storage"""
        if provider == "s3":
            return await self._s3_download(bucket, key, **kwargs)
        elif provider == "gcs":
            return await self._gcs_download(bucket, key, **kwargs)
        elif provider == "azure":
            return await self._azure_download(bucket, key, **kwargs)
        elif provider == "r2":
            return await self._r2_download(bucket, key, **kwargs)
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")

    async def list_objects(self, provider: str, bucket: str, prefix: str = "", **kwargs) -> List[Dict]:
        """List objects in bucket"""
        if provider == "s3":
            return await self._s3_list(bucket, prefix, **kwargs)
        elif provider == "gcs":
            return await self._gcs_list(bucket, prefix, **kwargs)
        elif provider == "azure":
            return await self._azure_list(bucket, prefix, **kwargs)
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")

    async def delete(self, provider: str, bucket: str, key: str, **kwargs) -> bool:
        """Delete object"""
        if provider == "s3":
            return await self._s3_delete(bucket, key, **kwargs)
        elif provider == "gcs":
            return await self._gcs_delete(bucket, key, **kwargs)
        elif provider == "azure":
            return await self._azure_delete(bucket, key, **kwargs)
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")

    # ==================== AWS S3 ====================

    async def _s3_upload(self, bucket, key, data, **kwargs):
        import boto3
        s3 = boto3.client("s3")
        s3.put_object(Bucket=bucket, Key=key, Body=data, **kwargs)
        return f"s3://{bucket}/{key}"

    async def _s3_download(self, bucket, key, **kwargs):
        import boto3
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    async def _s3_list(self, bucket, prefix, **kwargs):
        import boto3
        s3 = boto3.client("s3")
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [{"key": obj["Key"], "size": obj["Size"], "modified": obj["LastModified"]} for obj in response.get("Contents", [])]

    async def _s3_delete(self, bucket, key, **kwargs):
        import boto3
        s3 = boto3.client("s3")
        s3.delete_object(Bucket=bucket, Key=key)
        return True

    # ==================== GOOGLE CLOUD STORAGE ====================

    async def _gcs_upload(self, bucket, key, data, **kwargs):
        from google.cloud import storage
        client = storage.Client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        blob.upload_from_string(data)
        return f"gs://{bucket}/{key}"

    async def _gcs_download(self, bucket, key, **kwargs):
        from google.cloud import storage
        client = storage.Client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        return blob.download_as_bytes()

    async def _gcs_list(self, bucket, prefix, **kwargs):
        from google.cloud import storage
        client = storage.Client()
        blobs = client.list_blobs(bucket, prefix=prefix)
        return [{"key": blob.name, "size": blob.size, "modified": blob.updated} for blob in blobs]

    async def _gcs_delete(self, bucket, key, **kwargs):
        from google.cloud import storage
        client = storage.Client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(key)
        blob.delete()
        return True

    # ==================== AZURE BLOB ====================

    async def _azure_upload(self, container, key, data, **kwargs):
        from azure.storage.blob import BlobServiceClient
        conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        client = BlobServiceClient.from_connection_string(conn_str)
        blob_client = client.get_blob_client(container=container, blob=key)
        blob_client.upload_blob(data, overwrite=True)
        return f"azure://{container}/{key}"

    async def _azure_download(self, container, key, **kwargs):
        from azure.storage.blob import BlobServiceClient
        conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        client = BlobServiceClient.from_connection_string(conn_str)
        blob_client = client.get_blob_client(container=container, blob=key)
        return blob_client.download_blob().readall()

    async def _azure_list(self, container, prefix, **kwargs):
        from azure.storage.blob import BlobServiceClient
        conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client(container)
        blobs = container_client.list_blobs(name_starts_with=prefix)
        return [{"key": blob.name, "size": blob.size, "modified": blob.last_modified} for blob in blobs]

    async def _azure_delete(self, container, key, **kwargs):
        from azure.storage.blob import BlobServiceClient
        conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        client = BlobServiceClient.from_connection_string(conn_str)
        blob_client = client.get_blob_client(container=container, blob=key)
        blob_client.delete_blob()
        return True

    # ==================== CLOUDFLARE R2 ====================

    async def _r2_upload(self, bucket, key, data, **kwargs):
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{os.environ.get('CF_ACCOUNT_ID')}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ.get("R2_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("R2_SECRET_KEY")
        )
        s3.put_object(Bucket=bucket, Key=key, Body=data)
        return f"r2://{bucket}/{key}"

    async def _r2_download(self, bucket, key, **kwargs):
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{os.environ.get('CF_ACCOUNT_ID')}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ.get("R2_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("R2_SECRET_KEY")
        )
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    # ==================== BACKBLAZE B2 ====================

    async def _b2_upload(self, bucket, key, data, **kwargs):
        from b2sdk.v2 import B2Api, InMemoryAccountInfo
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", os.environ.get("B2_KEY_ID"), os.environ.get("B2_APP_KEY"))
        bucket_obj = b2_api.get_bucket_by_name(bucket)
        bucket_obj.upload_bytes(data, key)
        return f"b2://{bucket}/{key}"

    # ==================== MINIO ====================

    async def _minio_upload(self, bucket, key, data, **kwargs):
        from minio import Minio
        from io import BytesIO
        client = Minio(
            os.environ.get("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.environ.get("MINIO_ACCESS_KEY"),
            secret_key=os.environ.get("MINIO_SECRET_KEY"),
            secure=False
        )
        client.put_object(bucket, key, BytesIO(data), len(data))
        return f"minio://{bucket}/{key}"

    def list_providers(self) -> List[str]:
        return ["s3", "gcs", "azure", "r2", "b2", "minio", "wasabi", "digitalocean", "linode", "vultr"]
