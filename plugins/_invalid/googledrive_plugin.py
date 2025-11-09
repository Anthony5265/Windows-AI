"""
Google Drive Cloud Storage Plugin
Supports file operations like upload, download, list, delete, and folder management
"""

from typing import Dict, Any, Optional, List
import os
import io
import json


class GoogleDrivePlugin:
    """Plugin for Google Drive cloud storage operations"""

    name = "googledrive"
    version = "1.0.0"
    description = "Integration with Google Drive for file operations"
    author = "Windows AI Team"

    def __init__(self):
        self.service = None
        self._initialized = False
        self.credentials_path = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Google Drive plugin"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            # Get configuration
            self.credentials_path = (
                config.get("credentials_path") if config
                else os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
            )

            token_path = (
                config.get("token_path") if config
                else os.getenv("GOOGLE_DRIVE_TOKEN_PATH", "token.json")
            )

            scopes = ['https://www.googleapis.com/auth/drive']

            creds = None
            # Load existing token if available
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, scopes)

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path or not os.path.exists(self.credentials_path):
                        print("Google Drive credentials file not found. Please set GOOGLE_DRIVE_CREDENTIALS_PATH or provide credentials_path in config.")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, scopes)
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            # Build the service
            self.service = build('drive', 'v3', credentials=creds)
            self._initialized = True
            return True

        except ImportError as e:
            print(f"Required packages not installed: {e}. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        except Exception as e:
            print(f"Error initializing Google Drive plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Google Drive action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please configure Google Drive credentials."}

        try:
            if action == "upload_file":
                return self._upload_file(params)
            elif action == "download_file":
                return self._download_file(params)
            elif action == "list_files":
                return self._list_files(params)
            elif action == "delete_file":
                return self._delete_file(params)
            elif action == "create_folder":
                return self._create_folder(params)
            elif action == "get_file_info":
                return self._get_file_info(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _upload_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to Google Drive"""
        file_path = params.get("file_path")
        file_name = params.get("file_name", os.path.basename(file_path))
        folder_id = params.get("folder_id", "root")  # Default to root
        mime_type = params.get("mime_type", "application/octet-stream")

        if not file_path or not os.path.exists(file_path):
            return {"error": "File path not provided or file does not exist"}

        try:
            from googleapiclient.http import MediaFileUpload

            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime,modifiedTime'
            ).execute()

            return {
                "success": True,
                "file_id": file.get('id'),
                "file_name": file.get('name'),
                "file_size": file.get('size'),
                "created_time": file.get('createdTime'),
                "modified_time": file.get('modifiedTime')
            }

        except Exception as e:
            return {"error": f"Failed to upload file: {str(e)}"}

    def _download_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Download a file from Google Drive"""
        file_id = params.get("file_id")
        local_path = params.get("local_path")

        if not file_id:
            return {"error": "File ID not provided"}

        if not local_path:
            return {"error": "Local path not provided"}

        try:
            from googleapiclient.http import MediaIoBaseDownload

            request = self.service.files().get_media(fileId=file_id)
            with io.FileIO(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()

            # Get file metadata
            file_info = self.service.files().get(fileId=file_id, fields='name,size').execute()

            return {
                "success": True,
                "file_name": file_info.get('name'),
                "file_size": file_info.get('size'),
                "local_path": local_path
            }

        except Exception as e:
            return {"error": f"Failed to download file: {str(e)}"}

    def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a Google Drive folder"""
        folder_id = params.get("folder_id", "root")
        query = params.get("query", "")
        page_size = params.get("page_size", 100)
        order_by = params.get("order_by", "name")

        try:
            # Build query
            full_query = f"'{folder_id}' in parents and trashed = false"
            if query:
                full_query += f" and {query}"

            results = self.service.files().list(
                q=full_query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, size, mimeType, createdTime, modifiedTime)",
                orderBy=order_by
            ).execute()

            files = results.get('files', [])

            file_list = []
            for file in files:
                file_list.append({
                    "id": file.get('id'),
                    "name": file.get('name'),
                    "size": file.get('size'),
                    "mime_type": file.get('mimeType'),
                    "created_time": file.get('createdTime'),
                    "modified_time": file.get('modifiedTime')
                })

            return {
                "files": file_list,
                "count": len(file_list),
                "next_page_token": results.get('nextPageToken')
            }

        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    def _delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file from Google Drive"""
        file_id = params.get("file_id")

        if not file_id:
            return {"error": "File ID not provided"}

        try:
            self.service.files().delete(fileId=file_id).execute()
            return {"success": True, "file_id": file_id}

        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}

    def _create_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder in Google Drive"""
        folder_name = params.get("folder_name")
        parent_id = params.get("parent_id", "root")

        if not folder_name:
            return {"error": "Folder name not provided"}

        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name,createdTime'
            ).execute()

            return {
                "success": True,
                "folder_id": folder.get('id'),
                "folder_name": folder.get('name'),
                "created_time": folder.get('createdTime')
            }

        except Exception as e:
            return {"error": f"Failed to create folder: {str(e)}"}

    def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a file"""
        file_id = params.get("file_id")

        if not file_id:
            return {"error": "File ID not provided"}

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,size,mimeType,createdTime,modifiedTime,parents,webViewLink'
            ).execute()

            return {
                "id": file.get('id'),
                "name": file.get('name'),
                "size": file.get('size'),
                "mime_type": file.get('mimeType'),
                "created_time": file.get('createdTime'),
                "modified_time": file.get('modifiedTime'),
                "parents": file.get('parents', []),
                "web_view_link": file.get('webViewLink')
            }

        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.service = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = GoogleDrivePlugin
PLUGIN_NAME = "googledrive"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Google Drive cloud storage integration"
PLUGIN_ACTIONS = ["upload_file", "download_file", "list_files", "delete_file", "create_folder", "get_file_info"]