"""
YouTube API Plugin
Supports video upload and analytics retrieval
"""

from typing import Dict, Any, Optional, List
import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class YouTubePlugin:
    """Plugin for YouTube API integration"""

    name = "youtube"
    version = "1.0.0"
    description = "Integration with YouTube API for video upload and analytics"
    author = "Windows AI Team"

    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]

    def __init__(self):
        self.youtube = None
        self._initialized = False
        self.credentials = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the YouTube plugin"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            # Get configuration
            client_secrets_file = config.get("client_secrets_file") if config else None
            token_file = config.get("token_file", "token.json")

            if not client_secrets_file:
                client_secrets_file = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")
                if not client_secrets_file:
                    print("YouTube client secrets file not provided. Set YOUTUBE_CLIENT_SECRETS_FILE environment variable or pass in config.")
                    return False

            # Load or refresh credentials
            self.credentials = self._get_credentials(client_secrets_file, token_file)

            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    print("Failed to obtain valid credentials. Please run authentication flow.")
                    return False

                # Save the credentials for the next run
                with open(token_file, 'w') as token:
                    token.write(self.credentials.to_json())

            # Build the YouTube API client
            self.youtube = build('youtube', 'v3', credentials=self.credentials)

            self._initialized = True
            return True

        except ImportError as e:
            print(f"Required packages not installed: {e}. Install with: pip install google-api-python-client google-auth-oauthlib")
            return False
        except Exception as e:
            print(f"Error initializing YouTube plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a YouTube action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please configure YouTube API credentials."}

        try:
            if action == "upload_video":
                return self._upload_video(params)
            elif action == "get_analytics":
                return self._get_analytics(params)
            elif action == "get_video_info":
                return self._get_video_info(params)
            elif action == "list_videos":
                return self._list_videos(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _upload_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a video to YouTube"""
        file_path = params.get("file_path")
        title = params.get("title", "Uploaded Video")
        description = params.get("description", "")
        tags = params.get("tags", [])
        privacy_status = params.get("privacy_status", "private")  # private, public, unlisted

        if not file_path or not os.path.exists(file_path):
            return {"error": "Valid file path required"}

        try:
            # Create the request body
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22'  # People & Blogs category
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }

            # Create the media file upload object
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

            # Execute the upload request
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = request.execute()

            return {
                "video_id": response.get('id'),
                "title": response.get('snippet', {}).get('title'),
                "description": response.get('snippet', {}).get('description'),
                "published_at": response.get('snippet', {}).get('publishedAt'),
                "channel_id": response.get('snippet', {}).get('channelId'),
                "privacy_status": response.get('status', {}).get('privacyStatus'),
                "upload_status": response.get('status', {}).get('uploadStatus')
            }

        except Exception as e:
            return {"error": f"Failed to upload video: {str(e)}"}

    def _get_analytics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get analytics for a video or channel"""
        video_id = params.get("video_id")
        channel_id = params.get("channel_id")
        days = params.get("days", 30)  # Number of days to look back

        if not video_id and not channel_id:
            return {"error": "Either video_id or channel_id required"}

        try:
            if video_id:
                # Get video statistics
                request = self.youtube.videos().list(
                    part='statistics,snippet',
                    id=video_id
                )
                response = request.execute()

                if not response.get('items'):
                    return {"error": "Video not found"}

                video = response['items'][0]
                stats = video.get('statistics', {})

                return {
                    "video_id": video_id,
                    "title": video.get('snippet', {}).get('title'),
                    "view_count": int(stats.get('viewCount', 0)),
                    "like_count": int(stats.get('likeCount', 0)),
                    "dislike_count": int(stats.get('dislikeCount', 0)),
                    "favorite_count": int(stats.get('favoriteCount', 0)),
                    "comment_count": int(stats.get('commentCount', 0))
                }

            elif channel_id:
                # Get channel statistics
                request = self.youtube.channels().list(
                    part='statistics,snippet',
                    id=channel_id
                )
                response = request.execute()

                if not response.get('items'):
                    return {"error": "Channel not found"}

                channel = response['items'][0]
                stats = channel.get('statistics', {})

                return {
                    "channel_id": channel_id,
                    "title": channel.get('snippet', {}).get('title'),
                    "subscriber_count": int(stats.get('subscriberCount', 0)),
                    "video_count": int(stats.get('videoCount', 0)),
                    "view_count": int(stats.get('viewCount', 0))
                }

        except Exception as e:
            return {"error": f"Failed to get analytics: {str(e)}"}

    def _get_video_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a video"""
        video_id = params.get("video_id")

        if not video_id:
            return {"error": "video_id required"}

        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,status,contentDetails',
                id=video_id
            )
            response = request.execute()

            if not response.get('items'):
                return {"error": "Video not found"}

            video = response['items'][0]

            return {
                "video_id": video_id,
                "title": video.get('snippet', {}).get('title'),
                "description": video.get('snippet', {}).get('description'),
                "published_at": video.get('snippet', {}).get('publishedAt'),
                "channel_id": video.get('snippet', {}).get('channelId'),
                "channel_title": video.get('snippet', {}).get('channelTitle'),
                "tags": video.get('snippet', {}).get('tags', []),
                "duration": video.get('contentDetails', {}).get('duration'),
                "definition": video.get('contentDetails', {}).get('definition'),
                "view_count": int(video.get('statistics', {}).get('viewCount', 0)),
                "like_count": int(video.get('statistics', {}).get('likeCount', 0)),
                "comment_count": int(video.get('statistics', {}).get('commentCount', 0)),
                "privacy_status": video.get('status', {}).get('privacyStatus')
            }

        except Exception as e:
            return {"error": f"Failed to get video info: {str(e)}"}

    def _list_videos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List videos from a channel"""
        channel_id = params.get("channel_id")
        max_results = params.get("max_results", 10)
        order = params.get("order", "date")  # date, rating, relevance, title, videoCount, viewCount

        if not channel_id:
            return {"error": "channel_id required"}

        try:
            request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                maxResults=max_results,
                order=order,
                type='video'
            )
            response = request.execute()

            videos = []
            for item in response.get('items', []):
                videos.append({
                    "video_id": item.get('id', {}).get('videoId'),
                    "title": item.get('snippet', {}).get('title'),
                    "description": item.get('snippet', {}).get('description'),
                    "published_at": item.get('snippet', {}).get('publishedAt'),
                    "channel_title": item.get('snippet', {}).get('channelTitle'),
                    "thumbnail_url": item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url')
                })

            return {
                "videos": videos,
                "total_results": response.get('pageInfo', {}).get('totalResults', 0)
            }

        except Exception as e:
            return {"error": f"Failed to list videos: {str(e)}"}

    def _get_credentials(self, client_secrets_file: str, token_file: str) -> Optional[Credentials]:
        """Get valid credentials for YouTube API"""
        creds = None

        # Check if token file exists
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        return creds

    def cleanup(self):
        """Cleanup resources"""
        self.youtube = None
        self.credentials = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = YouTubePlugin
PLUGIN_NAME = "youtube"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with YouTube API for video management"
PLUGIN_ACTIONS = ["upload_video", "get_analytics", "get_video_info", "list_videos"]