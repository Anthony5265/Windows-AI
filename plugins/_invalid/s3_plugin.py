"""
Amazon S3 Cloud Storage Plugin
Supports bucket operations and file upload/download
"""

from typing import Dict, Any, Optional, List
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


class S3Plugin:
    """Plugin for Amazon S3 cloud storage operations"""

    name = "s3"
    version = "1.0.0"
    description = "Integration with Amazon S3 for bucket and file operations"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the S3 plugin"""
        try:
            # Get AWS credentials from config or environment
            aws_access_key_id = (
                config.get("aws_access_key_id") if config
                else os.getenv("AWS_ACCESS_KEY_ID")
            )
            aws_secret_access_key = (
                config.get("aws_secret_access_key") if config
                else os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            region_name = (
                config.get("region_name", "us-east-1") if config
                else os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )

            if not aws_access_key_id or not aws_secret_access_key:
                print("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or provide them in config.")
                return False

            # Create S3 client
            self.client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )

            # Test connection
            self.client.list_buckets()
            self._initialized = True
            return True

        except ImportError:
            print("boto3 package not installed. Install with: pip install boto3")
            return False
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"AWS credentials error: {e}")
            return False
        except Exception as e:
            print(f"Error initializing S3 plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an S3 action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please configure AWS credentials."}

        try:
            if action == "upload_file":
                return self._upload_file(params)
            elif action == "download_file":
                return self._download_file(params)
            elif action == "list_objects":
                return self._list_objects(params)
            elif action == "delete_object":
                return self._delete_object(params)
            elif action == "create_bucket":
                return self._create_bucket(params)
            elif action == "list_buckets":
                return self._list_buckets(params)
            elif action == "delete_bucket":
                return self._delete_bucket(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _upload_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to S3"""
        bucket_name = params.get("bucket_name")
        file_path = params.get("file_path")
        key = params.get("key")  # S3 object key (path in bucket)
        acl = params.get("acl", "private")  # Access control list

        if not bucket_name:
            return {"error": "Bucket name not provided"}

        if not file_path or not os.path.exists(file_path):
            return {"error": "File path not provided or file does not exist"}

        if not key:
            key = os.path.basename(file_path)

        try:
            # Upload file
            self.client.upload_file(
                file_path,
                bucket_name,
                key,
                ExtraArgs={'ACL': acl}
            )

            # Get object metadata
            response = self.client.head_object(Bucket=bucket_name, Key=key)

            return {
                "success": True,
                "bucket_name": bucket_name,
                "key": key,
                "size": response.get('ContentLength'),
                "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                "etag": response.get('ETag')
            }

        except Exception as e:
            return {"error": f"Failed to upload file: {str(e)}"}

    def _download_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Download a file from S3"""
        bucket_name = params.get("bucket_name")
        key = params.get("key")
        local_path = params.get("local_path")

        if not bucket_name:
            return {"error": "Bucket name not provided"}

        if not key:
            return {"error": "Object key not provided"}

        if not local_path:
            return {"error": "Local path not provided"}

        try:
            # Download file
            self.client.download_file(bucket_name, key, local_path)

            # Get file size
            file_size = os.path.getsize(local_path)

            return {
                "success": True,
                "bucket_name": bucket_name,
                "key": key,
                "local_path": local_path,
                "size": file_size
            }

        except Exception as e:
            return {"error": f"Failed to download file: {str(e)}"}

    def _list_objects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List objects in an S3 bucket"""
        bucket_name = params.get("bucket_name")
        prefix = params.get("prefix", "")  # Filter by prefix
        max_keys = params.get("max_keys", 1000)

        if not bucket_name:
            return {"error": "Bucket name not provided"}

        try:
            response = self.client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        "key": obj.get('Key'),
                        "size": obj.get('Size'),
                        "last_modified": obj.get('LastModified').isoformat() if obj.get('LastModified') else None,
                        "etag": obj.get('ETag')
                    })

            return {
                "objects": objects,
                "count": len(objects),
                "is_truncated": response.get('IsTruncated', False),
                "next_continuation_token": response.get('NextContinuationToken')
            }

        except Exception as e:
            return {"error": f"Failed to list objects: {str(e)}"}

    def _delete_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an object from S3"""
        bucket_name = params.get("bucket_name")
        key = params.get("key")

        if not bucket_name:
            return {"error": "Bucket name not provided"}

        if not key:
            return {"error": "Object key not provided"}

        try:
            self.client.delete_object(Bucket=bucket_name, Key=key)
            return {"success": True, "bucket_name": bucket_name, "key": key}

        except Exception as e:
            return {"error": f"Failed to delete object: {str(e)}"}

    def _create_bucket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an S3 bucket"""
        bucket_name = params.get("bucket_name")
        region = params.get("region")

        if not bucket_name:
            return {"error": "Bucket name not provided"}

        try:
            if region and region != 'us-east-1':
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            else:
                self.client.create_bucket(Bucket=bucket_name)

            return {
                "success": True,
                "bucket_name": bucket_name,
                "region": region or 'us-east-1'
            }

        except Exception as e:
            return {"error": f"Failed to create bucket: {str(e)}"}

    def _list_buckets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all S3 buckets"""
        try:
            response = self.client.list_buckets()

            buckets = []
            for bucket in response['Buckets']:
                buckets.append({
                    "name": bucket.get('Name'),
                    "creation_date": bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None
                })

            return {
                "buckets": buckets,
                "count": len(buckets)
            }

        except Exception as e:
            return {"error": f"Failed to list buckets: {str(e)}"}

    def _delete_bucket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an S3 bucket (must be empty)"""
        bucket_name = params.get("bucket_name")

        if not bucket_name:
            return {"error": "Bucket name not provided"}

        try:
            self.client.delete_bucket(Bucket=bucket_name)
            return {"success": True, "bucket_name": bucket_name}

        except Exception as e:
            return {"error": f"Failed to delete bucket: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = S3Plugin
PLUGIN_NAME = "s3"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Amazon S3 cloud storage integration"
PLUGIN_ACTIONS = ["upload_file", "download_file", "list_objects", "delete_object", "create_bucket", "list_buckets", "delete_bucket"]