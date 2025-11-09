"""
LinkedIn Social Media Plugin
Supports profile updates and post sharing
"""

from typing import Dict, Any, Optional, List
import os


class LinkedInPlugin:
    """Plugin for LinkedIn API integration"""
    
    name = "linkedin"
    version = "1.0.0"
    description = "Integration with LinkedIn API for profile updates and post sharing"
    author = "Windows AI Team"
    
    def __init__(self):
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LinkedIn plugin"""
        try:
            import requests
            
            # Get credentials from config or environment
            self.client_id = (
                config.get("client_id") if config 
                else os.getenv("LINKEDIN_CLIENT_ID")
            )
            self.client_secret = (
                config.get("client_secret") if config 
                else os.getenv("LINKEDIN_CLIENT_SECRET")
            )
            self.access_token = (
                config.get("access_token") if config 
                else os.getenv("LINKEDIN_ACCESS_TOKEN")
            )
            
            if not all([self.client_id, self.client_secret, self.access_token]):
                return False
                
            # Initialize requests session with LinkedIn API
            self.client = requests.Session()
            self.client.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            })
            
            self._initialized = True
            return True
            
        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing LinkedIn plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LinkedIn action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide LinkedIn API credentials."}
        
        try:
            if action == "share_post":
                return self._share_post(params)
            elif action == "update_profile":
                return self._update_profile(params)
            elif action == "get_profile":
                return self._get_profile(params)
            elif action == "get_posts":
                return self._get_posts(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _share_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Share a post on LinkedIn"""
        text = params.get("text", "")
        if not text:
            return {"error": "Post text is required"}
        
        visibility = params.get("visibility", "PUBLIC")  # PUBLIC, CONNECTIONS
        owner = params.get("owner")  # Optional: specify owner URN
        
        try:
            # Get current user profile if owner not specified
            if not owner:
                profile_response = self._get_profile({})
                if "error" in profile_response:
                    return {"error": "Failed to get user profile"}
                owner = profile_response.get("id")
            
            # Prepare post data
            post_data = {
                "author": f"urn:li:person:{owner}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            # Create post
            response = self.client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                json=post_data
            )
            
            if response.status_code == 201:
                post_id = response.headers.get('X-RestLi-Id', response.json().get('id'))
                return {
                    "success": True,
                    "post_id": post_id,
                    "text": text,
                    "visibility": visibility
                }
            else:
                return {"error": f"Failed to create post: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to share post: {str(e)}"}
    
    def _update_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update LinkedIn profile"""
        updates = params.get("updates", {})
        if not updates:
            return {"error": "Profile updates are required"}
        
        try:
            # Get current profile ID
            profile_response = self._get_profile({})
            if "error" in profile_response:
                return {"error": "Failed to get user profile"}
            
            profile_id = profile_response.get("id")
            
            # Prepare update data
            update_data = {}
            
            if "headline" in updates:
                update_data["headline"] = updates["headline"]
            
            if "summary" in updates:
                update_data["summary"] = updates["summary"]
            
            if "location" in updates:
                update_data["location"] = updates["location"]
            
            if "industry" in updates:
                update_data["industry"] = updates["industry"]
            
            # Update profile
            response = self.client.patch(
                f"https://api.linkedin.com/v2/people/{profile_id}",
                json=update_data
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "updated_fields": list(updates.keys()),
                    "profile_id": profile_id
                }
            else:
                return {"error": f"Failed to update profile: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to update profile: {str(e)}"}
    
    def _get_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get LinkedIn profile information"""
        fields = params.get("fields", ["id", "firstName", "lastName", "headline", "summary"])
        
        try:
            response = self.client.get(
                "https://api.linkedin.com/v2/people/~:({})".format(",".join(fields))
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Format profile data
                profile = {
                    "id": data.get("id"),
                    "firstName": data.get("firstName", {}).get("localized", {}).get("en_US", ""),
                    "lastName": data.get("lastName", {}).get("localized", {}).get("en_US", ""),
                    "headline": data.get("headline", ""),
                    "summary": data.get("summary", ""),
                    "profile_url": f"https://linkedin.com/in/{data.get('vanityName', '')}" if data.get("vanityName") else None
                }
                
                return profile
            else:
                return {"error": f"Failed to get profile: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to get profile: {str(e)}"}
    
    def _get_posts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get user's LinkedIn posts"""
        count = params.get("count", 10)
        start = params.get("start", 0)
        
        try:
            # Get current user profile
            profile_response = self._get_profile({})
            if "error" in profile_response:
                return {"error": "Failed to get user profile"}
            
            profile_id = profile_response.get("id")
            
            # Get posts
            response = self.client.get(
                f"https://api.linkedin.com/v2/socialActions/{profile_id}",
                params={
                    "q": "actors",
                    "actors": f"urn:li:person:{profile_id}",
                    "count": count,
                    "start": start
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                for element in data.get("elements", []):
                    posts.append({
                        "id": element.get("id"),
                        "created_at": element.get("created", {}).get("time"),
                        "activity": element.get("activity", ""),
                        "actor": element.get("actor", "")
                    })
                
                return {
                    "posts": posts,
                    "count": len(posts),
                    "total": data.get("paging", {}).get("total", 0)
                }
            else:
                return {"error": f"Failed to get posts: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to get posts: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.client:
            self.client.close()
        self.client = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = LinkedInPlugin
PLUGIN_NAME = "linkedin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with LinkedIn API for profile updates and post sharing"
PLUGIN_ACTIONS = ["share_post", "update_profile", "get_profile", "get_posts"]