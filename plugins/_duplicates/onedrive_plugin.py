"""
OneDrive Cloud Storage Plugin
Supports file operations like upload, download, list, delete, and folder management
"""

from typing import Dict, Any, Optional, List
import os
import io
import json
import requests
from datetime import datetime, timedelta


class OneDrivePlugin:
    """Plugin for OneDrive cloud storage operations"""

    name = "onedrive"
    version = "1.0.0"
    description = "Integration with Microsoft OneDrive for file operations"
    author = "Windows AI Team"

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self._initialized = False
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = "http://localhost:8080"
        self.scopes = ["https://graph.microsoft.com/Files.ReadWrite", "https://graph.microsoft.com/User.Read"]
        self.token_expiry = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the OneDrive plugin"""
        try:
            # Get configuration
            self.client_id = (
                config.get("client_id") if config
                else os.getenv("ONEDRIVE_CLIENT_ID")
            )
            self.client_secret = (
                config.get("client_secret") if config
                else os.getenv("ONEDRIVE_CLIENT_SECRET")
            )
            
            # Try to load saved tokens
            token_path = (
                config.get("token_path") if config
                else os.getenv("ONEDRIVE_TOKEN_PATH", "onedrive_token.json")
            )

            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token_data = json.load(f)
                    self.access_token = token_data.get("access_token")
                    self.refresh_token = token_data.get("refresh_token")
                    expiry_str = token_data.get("expiry")
                    if expiry_str:
                        self.token_expiry = datetime.fromisoformat(expiry_str)

            # Check if token needs refresh
            if self.access_token and self.token_expiry and datetime.now() >= self.token_expiry:
                if not self._refresh_access_token():
                    print("Token refresh failed, please re-authenticate")
                    return False

            # If no valid token, start OAuth flow
            if not self.access_token:
                if not self.client_id or not self.client_secret:
                    print("OneDrive client credentials not found. Please set ONEDRIVE_CLIENT_ID and ONEDRIVE_CLIENT_SECRET or provide in config.")
                    return False
                
                print("Please authenticate with OneDrive:")
                auth_url = self._get_auth_url()
                print(f"Visit this URL to authorize: {auth_url}")
                
                auth_code = input("Enter the authorization code: ")
                if not self._exchange_code_for_token(auth_code):
                    return False
                
                # Save tokens
                self._save_tokens(token_path)

            # Test the connection
            if not self._test_connection():
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing OneDrive plugin: {e}")
            return False

    def _get_auth_url(self) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "response_mode": "query"
        }
        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{requests.compat.urlencode(params)}"

    def _exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token"""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
                "scope": " ".join(self.scopes)
            }
            
            response = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")
            
            # Set expiry time (tokens typically last 1 hour)
            self.token_expiry = datetime.now() + timedelta(hours=1)
            
            return True
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return False

    def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False
            
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(self.scopes)
            }
            
            response = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]
            
            self.token_expiry = datetime.now() + timedelta(hours=1)
            return True
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False

    def _save_tokens(self, token_path: str):
        """Save tokens to file"""
        try:
            token_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expiry": self.token_expiry.isoformat() if self.token_expiry else None
            }
            with open(token_path, 'w') as f:
                json.dump(token_data, f)
        except Exception as e:
            print(f"Error saving tokens: {e}")

    def _test_connection(self) -> bool:
        """Test connection to OneDrive"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a OneDrive action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please configure OneDrive credentials."}

        # Check if token needs refresh
        if self.token_expiry and datetime.now() >= self.token_expiry:
            if not self._refresh_access_token():
                return {"error": "Token expired and refresh failed. Please re-authenticate."}

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
            elif action == "sync_folder":
                return self._sync_folder(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization"""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _upload_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to OneDrive"""
        file_path = params.get("file_path")
        file_name = params.get("file_name", os.path.basename(file_path))
        parent_path = params.get("parent_path", "/drive/root:/")

        if not file_path or not os.path.exists(file_path):
            return {"error": "File path not provided or file does not exist"}

        try:
            # For small files (<4MB), use simple upload
            file_size = os.path.getsize(file_path)
            
            if file_size < 4 * 1024 * 1024:  # 4MB
                return self._simple_upload(file_path, file_name, parent_path)
            else:
                return self._resumable_upload(file_path, file_name, parent_path)

        except Exception as e:
            return {"error": f"Failed to upload file: {str(e)}"}

    def _simple_upload(self, file_path: str, file_name: str, parent_path: str) -> Dict[str, Any]:
        """Simple upload for small files"""
        headers = self._get_headers()
        
        # Construct the upload URL
        upload_url = f"https://graph.microsoft.com/v1.0{parent_path}{file_name}:/content"
        
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, headers=headers, data=f)
            response.raise_for_status()
            
        file_data = response.json()
        return {
            "success": True,
            "file_id": file_data.get('id'),
            "file_name": file_data.get('name'),
            "file_size": file_data.get('size'),
            "created_time": file_data.get('createdDateTime'),
            "modified_time": file_data.get('lastModifiedDateTime'),
            "web_url": file_data.get('webUrl')
        }

    def _resumable_upload(self, file_path: str, file_name: str, parent_path: str) -> Dict[str, Any]:
        """Resumable upload for large files"""
        headers = self._get_headers()
        
        # Create upload session
        upload_url = f"https://graph.microsoft.com/v1.0{parent_path}{file_name}:/createUploadSession"
        response = requests.post(upload_url, headers=headers, json={"@microsoft.graph.conflictBehavior": "replace"})
        response.raise_for_status()
        
        upload_session = response.json()
        upload_url = upload_session['uploadUrl']
        
        # Upload file in chunks
        chunk_size = 320 * 1024 * 1024  # 320MB chunks
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as f:
            for chunk_start in range(0, file_size, chunk_size):
                chunk_end = min(chunk_start + chunk_size - 1, file_size - 1)
                chunk_data = f.read(chunk_size)
                
                content_range = f"bytes {chunk_start}-{chunk_end}/{file_size}"
                chunk_headers = {
                    **headers,
                    "Content-Range": content_range,
                    "Content-Length": str(len(chunk_data))
                }
                
                response = requests.put(upload_url, headers=chunk_headers, data=chunk_data)
                
                if response.status_code == 202:  # Continue uploading
                    continue
                elif response.status_code == 200:  # Upload complete
                    file_data = response.json()
                    return {
                        "success": True,
                        "file_id": file_data.get('id'),
                        "file_name": file_data.get('name'),
                        "file_size": file_data.get('size'),
                        "created_time": file_data.get('createdDateTime'),
                        "modified_time": file_data.get('lastModifiedDateTime'),
                        "web_url": file_data.get('webUrl')
                    }
                else:
                    response.raise_for_status()

    def _download_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Download a file from OneDrive"""
        file_id = params.get("file_id")
        local_path = params.get("local_path")

        if not file_id:
            return {"error": "File ID not provided"}

        if not local_path:
            return {"error": "Local path not provided"}

        try:
            headers = self._get_headers()
            
            # Get download URL
            response = requests.get(f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}", headers=headers)
            response.raise_for_status()
            
            file_info = response.json()
            download_url = file_info.get('@microsoft.graph.downloadUrl')
            
            if not download_url:
                return {"error": "Download URL not available"}
            
            # Download the file
            response = requests.get(download_url)
            response.raise_for_status()
            
            # Save to local path
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return {
                "success": True,
                "file_name": file_info.get('name'),
                "file_size": file_info.get('size'),
                "local_path": local_path
            }

        except Exception as e:
            return {"error": f"Failed to download file: {str(e)}"}

    def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a OneDrive folder"""
        folder_id = params.get("folder_id", "root")
        query = params.get("query", "")
        page_size = params.get("page_size", 100)

        try:
            headers = self._get_headers()
            
            # Build the endpoint URL
            if folder_id == "root":
                endpoint = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            else:
                endpoint = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"
            
            # Add query parameters
            params_str = f"?$top={page_size}&$select=id,name,size,file,folder,createdDateTime,lastModifiedDateTime"
            if query:
                params_str += f"&$filter={query}"
            
            response = requests.get(endpoint + params_str, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            files = data.get('value', [])
            
            file_list = []
            for file in files:
                file_info = {
                    "id": file.get('id'),
                    "name": file.get('name'),
                    "size": file.get('size'),
                    "created_time": file.get('createdDateTime'),
                    "modified_time": file.get('lastModifiedDateTime')
                }
                
                if 'file' in file:
                    file_info["mime_type"] = file['file'].get('mimeType')
                    file_info["type"] = "file"
                elif 'folder' in file:
                    file_info["type"] = "folder"
                
                file_list.append(file_info)
            
            return {
                "files": file_list,
                "count": len(file_list),
                "next_page_token": data.get('@odata.nextLink')
            }

        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    def _delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file from OneDrive"""
        file_id = params.get("file_id")

        if not file_id:
            return {"error": "File ID not provided"}

        try:
            headers = self._get_headers()
            response = requests.delete(f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}", headers=headers)
            response.raise_for_status()
            
            return {"success": True, "file_id": file_id}

        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}

    def _create_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder in OneDrive"""
        folder_name = params.get("folder_name")
        parent_id = params.get("parent_id", "root")

        if not folder_name:
            return {"error": "Folder name not provided"}

        try:
            headers = self._get_headers()
            
            # Determine parent endpoint
            if parent_id == "root":
                endpoint = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            else:
                endpoint = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_id}/children"
            
            folder_data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            response = requests.post(endpoint, headers=headers, json=folder_data)
            response.raise_for_status()
            
            folder = response.json()
            
            return {
                "success": True,
                "folder_id": folder.get('id'),
                "folder_name": folder.get('name'),
                "created_time": folder.get('createdDateTime'),
                "web_url": folder.get('webUrl')
            }

        except Exception as e:
            return {"error": f"Failed to create folder: {str(e)}"}

    def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a file"""
        file_id = params.get("file_id")

        if not file_id:
            return {"error": "File ID not provided"}

        try:
            headers = self._get_headers()
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}",
                headers=headers
            )
            response.raise_for_status()
            
            file = response.json()
            
            return {
                "id": file.get('id'),
                "name": file.get('name'),
                "size": file.get('size'),
                "created_time": file.get('createdDateTime'),
                "modified_time": file.get('lastModifiedDateTime'),
                "web_url": file.get('webUrl'),
                "parent_id": file.get('parentReference', {}).get('id') if file.get('parentReference') else None
            }

        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}

    def _sync_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync a local folder with OneDrive"""
        local_path = params.get("local_path")
        onedrive_path = params.get("onedrive_path", "/drive/root:/")
        sync_direction = params.get("direction", "both")  # "up", "down", or "both"

        if not local_path or not os.path.exists(local_path):
            return {"error": "Local path not provided or does not exist"}

        try:
            sync_results = {
                "uploaded": [],
                "downloaded": [],
                "errors": []
            }
            
            # Get OneDrive folder contents
            onedrive_files_result = self._list_files({"folder_id": "root" if onedrive_path == "/drive/root:/" else onedrive_path})
            if "error" in onedrive_files_result:
                return onedrive_files_result
            
            onedrive_files = {f["name"]: f for f in onedrive_files_result["files"]}
            local_files = set(os.listdir(local_path))
            
            # Upload new/modified local files
            if sync_direction in ["up", "both"]:
                for local_file in local_files:
                    local_file_path = os.path.join(local_path, local_file)
                    if os.path.isfile(local_file_path):
                        if local_file not in onedrive_files:
                            # Upload new file
                            upload_result = self._upload_file({
                                "file_path": local_file_path,
                                "parent_path": onedrive_path
                            })
                            if upload_result.get("success"):
                                sync_results["uploaded"].append(local_file)
                            else:
                                sync_results["errors"].append(f"Failed to upload {local_file}: {upload_result.get('error')}")
            
            # Download new/modified OneDrive files
            if sync_direction in ["down", "both"]:
                for onedrive_file_name, onedrive_file in onedrive_files.items():
                    if onedrive_file.get("type") == "file" and onedrive_file_name not in local_files:
                        # Download new file
                        download_result = self._download_file({
                            "file_id": onedrive_file["id"],
                            "local_path": os.path.join(local_path, onedrive_file_name)
                        })
                        if download_result.get("success"):
                            sync_results["downloaded"].append(onedrive_file_name)
                        else:
                            sync_results["errors"].append(f"Failed to download {onedrive_file_name}: {download_result.get('error')}")
            
            return {
                "success": True,
                "sync_results": sync_results,
                "uploaded_count": len(sync_results["uploaded"]),
                "downloaded_count": len(sync_results["downloaded"]),
                "error_count": len(sync_results["errors"])
            }

        except Exception as e:
            return {"error": f"Failed to sync folder: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.access_token = None
        self.refresh_token = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = OneDrivePlugin
PLUGIN_NAME = "onedrive"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Microsoft OneDrive cloud storage integration"
PLUGIN_ACTIONS = ["upload_file", "download_file", "list_files", "delete_file", "create_folder", "get_file_info", "sync_folder"]