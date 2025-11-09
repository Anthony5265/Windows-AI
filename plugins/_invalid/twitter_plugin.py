"""
Twitter/X Social Media Plugin
Supports posting tweets and reading timeline
"""

from typing import Dict, Any, Optional, List
import os


class TwitterPlugin:
    """Plugin for Twitter/X API integration"""
    
    name = "twitter"
    version = "1.0.0"
    description = "Integration with Twitter/X API for posting and timeline reading"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.api_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.access_token_secret: Optional[str] = None
        self.bearer_token: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Twitter plugin"""
        try:
            import tweepy
            
            # Get credentials from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("TWITTER_API_KEY")
            )
            self.api_secret = (
                config.get("api_secret") if config 
                else os.getenv("TWITTER_API_SECRET")
            )
            self.access_token = (
                config.get("access_token") if config 
                else os.getenv("TWITTER_ACCESS_TOKEN")
            )
            self.access_token_secret = (
                config.get("access_token_secret") if config 
                else os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
            )
            self.bearer_token = (
                config.get("bearer_token") if config 
                else os.getenv("TWITTER_BEARER_TOKEN")
            )
            
            if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                return False
                
            # Initialize Tweepy client
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token
            )
            
            self._initialized = True
            return True
            
        except ImportError:
            print("tweepy package not installed. Install with: pip install tweepy")
            return False
        except Exception as e:
            print(f"Error initializing Twitter plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Twitter action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Twitter API credentials."}
        
        try:
            if action == "post":
                return self._post_tweet(params)
            elif action == "read_timeline":
                return self._read_timeline(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _post_tweet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post a tweet"""
        text = params.get("text", "")
        if not text:
            return {"error": "Tweet text is required"}
        
        try:
            response = self.client.create_tweet(text=text)
            return {
                "success": True,
                "tweet_id": response.data["id"],
                "text": text
            }
        except Exception as e:
            return {"error": f"Failed to post tweet: {str(e)}"}
    
    def _read_timeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read home timeline"""
        max_results = params.get("max_results", 10)
        if max_results > 100:
            max_results = 100  # API limit
        
        try:
            response = self.client.get_home_timeline(max_results=max_results)
            tweets = []
            for tweet in response.data:
                tweets.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "public_metrics": tweet.public_metrics
                })
            
            return {
                "tweets": tweets,
                "count": len(tweets)
            }
        except Exception as e:
            return {"error": f"Failed to read timeline: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = TwitterPlugin
PLUGIN_NAME = "twitter"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Twitter/X API for posting and timeline reading"
PLUGIN_ACTIONS = ["post", "read_timeline"]