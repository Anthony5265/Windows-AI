"""
Azure Blob Storage Cloud Storage Plugin
Supports blob operations like upload, download, list, delete, and container management
"""

from typing import Dict, Any, Optional, List
import os
import io


class AzureBlobPlugin:
    """Plugin for Azure Blob Storage operations"""

    name = "azure_blob"
    version = "1.0.0"
    description = "Integration with Azure Blob Storage for blob operations"
    author = "Windows AI Team"

    def __init__(self):
        self.blob_service_client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Azure Blob Storage plugin"""
        try:
            from azure.storage.blob import BlobServiceClient

            # Get configuration
            connection_string = (
                config.get("connection_string") if config
                else os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            )

            account_url = (
                config.get("account_url") if config
                else os.getenv("AZURE_STORAGE_ACCOUNT_URL")
            )

            account_name = (
                config.get("account_name") if config
                else os.getenv("AZURE_STORAGE_ACCOUNT")
            )

            account_key = (
                config.get("account_key") if config
                else os.getenv("AZURE_STORAGE_KEY")
            )

            if connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            elif account_url and account_name and account_key:
                account_url_full = f"https://{account_name}.blob.core.windows.net"
                if account_url:
                    account_url_full = account_url
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url_full,
                    credential=account_key
                )
            else:
                print("Azure Blob Storage credentials not provided. Set AZURE_STORAGE_CONNECTION_STRING or provide account_url, account_name, and account_key in config.")
                return False

            self._initialized = True
            return True

        except ImportError as e:
            print(f"Required packages not installed: {e}. Install with: pip install azure-storage-blob azure-identity")
            return False
        except Exception as e:
            print(f"Error initializing Azure Blob Storage plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Azure Blob Storage action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please configure Azure Blob Storage credentials."}

        try:
            if action == "upload_blob":
                return self._upload_blob(params)
            elif action == "download_blob":
                return self._download_blob(params)
            elif action == "list_blobs":
                return self._list_blobs(params)
            elif action == "delete_blob":
                return self._delete_blob(params)
            elif action == "create_container":
                return self._create_container(params)
            elif action == "delete_container":
                return self._delete_container(params)
            elif action == "get_blob_properties":
                return self._get_blob_properties(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _upload_blob(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a blob to Azure Blob Storage"""
        container_name = params.get("container_name")
        blob_name = params.get("blob_name")
        file_path = params.get("file_path")
        overwrite = params.get("overwrite", True)

        if not container_name:
            return {"error": "Container name not provided"}

        if not blob_name:
            return {"error": "Blob name not provided"}

        if not file_path or not os.path.exists(file_path):
            return {"error": "File path not provided or file does not exist"}

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )

            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=overwrite)

            # Get blob properties
            properties = blob_client.get_blob_properties()

            return {
                "success": True,
                "blob_name": blob_name,
                "container_name": container_name,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                "etag": properties.etag
            }

        except Exception as e:
            return {"error": f"Failed to upload blob: {str(e)}"}

    def _download_blob(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Download a blob from Azure Blob Storage"""
        container_name = params.get("container_name")
        blob_name = params.get("blob_name")
        local_path = params.get("local_path")

        if not container_name:
            return {"error": "Container name not provided"}

        if not blob_name:
            return {"error": "Blob name not provided"}

        if not local_path:
            return {"error": "Local path not provided"}

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )

            with open(local_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())

            # Get blob properties
            properties = blob_client.get_blob_properties()

            return {
                "success": True,
                "blob_name": blob_name,
                "container_name": container_name,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                "local_path": local_path
            }

        except Exception as e:
            return {"error": f"Failed to download blob: {str(e)}"}

    def _list_blobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List blobs in an Azure container"""
        container_name = params.get("container_name")
        prefix = params.get("prefix", "")
        max_results = params.get("max_results", 100)

        if not container_name:
            return {"error": "Container name not provided"}

        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_list = container_client.list_blobs(name_starts_with=prefix, max_results=max_results)

            blobs = []
            for blob in blob_list:
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "etag": blob.etag,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None
                })

            return {
                "blobs": blobs,
                "count": len(blobs),
                "container_name": container_name
            }

        except Exception as e:
            return {"error": f"Failed to list blobs: {str(e)}"}

    def _delete_blob(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a blob from Azure Blob Storage"""
        container_name = params.get("container_name")
        blob_name = params.get("blob_name")

        if not container_name:
            return {"error": "Container name not provided"}

        if not blob_name:
            return {"error": "Blob name not provided"}

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            blob_client.delete_blob()

            return {
                "success": True,
                "blob_name": blob_name,
                "container_name": container_name
            }

        except Exception as e:
            return {"error": f"Failed to delete blob: {str(e)}"}

    def _create_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a container in Azure Blob Storage"""
        container_name = params.get("container_name")
        public_access = params.get("public_access", "off")  # off, blob, container

        if not container_name:
            return {"error": "Container name not provided"}

        try:
            from azure.storage.blob import PublicAccess

            access_type = {
                "off": None,
                "blob": PublicAccess.Blob,
                "container": PublicAccess.Container
            }.get(public_access, None)

            container_client = self.blob_service_client.create_container(
                container_name, public_access=access_type
            )

            return {
                "success": True,
                "container_name": container_name,
                "public_access": public_access
            }

        except Exception as e:
            return {"error": f"Failed to create container: {str(e)}"}

    def _delete_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a container from Azure Blob Storage"""
        container_name = params.get("container_name")

        if not container_name:
            return {"error": "Container name not provided"}

        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            container_client.delete_container()

            return {
                "success": True,
                "container_name": container_name
            }

        except Exception as e:
            return {"error": f"Failed to delete container: {str(e)}"}

    def _get_blob_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get properties of a blob"""
        container_name = params.get("container_name")
        blob_name = params.get("blob_name")

        if not container_name:
            return {"error": "Container name not provided"}

        if not blob_name:
            return {"error": "Blob name not provided"}

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            properties = blob_client.get_blob_properties()

            return {
                "name": properties.name,
                "container": container_name,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                "etag": properties.etag,
                "content_type": properties.content_settings.content_type if properties.content_settings else None,
                "content_encoding": properties.content_settings.content_encoding if properties.content_settings else None,
                "content_language": properties.content_settings.content_language if properties.content_settings else None
            }

        except Exception as e:
            return {"error": f"Failed to get blob properties: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.blob_service_client = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = AzureBlobPlugin
PLUGIN_NAME = "azure_blob"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Azure Blob Storage cloud storage integration"
PLUGIN_ACTIONS = ["upload_blob", "download_blob", "list_blobs", "delete_blob", "create_container", "delete_container", "get_blob_properties"]