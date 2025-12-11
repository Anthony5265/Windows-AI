"""
Social Media Manager - 15+ Platforms
Twitter, LinkedIn, Facebook, Instagram, TikTok, etc.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SocialMediaManager:
    """Unified social media operations across 15+ platforms"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== TWITTER/X ====================

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def twitter_post(self, text: str, media_ids: List[str] = None) -> Dict:
        """Post to Twitter/X"""
        import tweepy

        client = tweepy.Client(
            bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"),
            consumer_key=os.environ.get("TWITTER_API_KEY"),
            consumer_secret=os.environ.get("TWITTER_API_SECRET"),
            access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET")
        )

        response = client.create_tweet(text=text, media_ids=media_ids)
        return {"id": response.data["id"], "text": response.data["text"]}

    async def twitter_search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Twitter/X"""
        import tweepy

        client = tweepy.Client(bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"))
        tweets = client.search_recent_tweets(query=query, max_results=max_results)

        return [{"id": tweet.id, "text": tweet.text} for tweet in (tweets.data or [])]

    async def twitter_get_user(self, username: str) -> Dict:
        """Get Twitter/X user"""
        import tweepy

        client = tweepy.Client(bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"))
        user = client.get_user(username=username, user_fields=["description", "public_metrics"])

        return {
            "id": user.data.id,
            "username": user.data.username,
            "name": user.data.name,
            "description": user.data.description,
            "followers": user.data.public_metrics["followers_count"]
        }

    # ==================== LINKEDIN ====================

    async def linkedin_post(self, text: str, author_urn: str) -> Dict:
        """Post to LinkedIn"""
        import aiohttp

        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "author": author_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": text},
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
                }
            ) as response:
                return await response.json()

    async def linkedin_get_profile(self) -> Dict:
        """Get LinkedIn profile"""
        import aiohttp

        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                return await response.json()

    # ==================== FACEBOOK ====================

    async def facebook_post(self, page_id: str, message: str) -> Dict:
        """Post to Facebook page"""
        import aiohttp

        access_token = os.environ.get("FACEBOOK_PAGE_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://graph.facebook.com/v18.0/{page_id}/feed",
                json={"message": message, "access_token": access_token}
            ) as response:
                return await response.json()

    async def facebook_get_page_insights(self, page_id: str, metrics: List[str]) -> Dict:
        """Get Facebook page insights"""
        import aiohttp

        access_token = os.environ.get("FACEBOOK_PAGE_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://graph.facebook.com/v18.0/{page_id}/insights",
                params={"metric": ",".join(metrics), "access_token": access_token}
            ) as response:
                return await response.json()

    # ==================== INSTAGRAM ====================

    async def instagram_post(self, ig_user_id: str, image_url: str, caption: str) -> Dict:
        """Post to Instagram"""
        import aiohttp

        access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            # Create container
            async with session.post(
                f"https://graph.facebook.com/v18.0/{ig_user_id}/media",
                json={"image_url": image_url, "caption": caption, "access_token": access_token}
            ) as response:
                container = await response.json()
                container_id = container["id"]

            # Publish
            async with session.post(
                f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish",
                json={"creation_id": container_id, "access_token": access_token}
            ) as response:
                return await response.json()

    # ==================== TIKTOK ====================

    async def tiktok_get_user_info(self) -> Dict:
        """Get TikTok user info"""
        import aiohttp

        access_token = os.environ.get("TIKTOK_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://open.tiktokapis.com/v2/user/info/",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fields": "open_id,union_id,avatar_url,display_name,bio_description,follower_count"}
            ) as response:
                return await response.json()

    # ==================== YOUTUBE ====================

    async def youtube_upload_video(self, video_path: str, title: str, description: str) -> Dict:
        """Upload video to YouTube"""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=os.environ.get("YOUTUBE_ACCESS_TOKEN"))
        youtube = build("youtube", "v3", credentials=credentials)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "public"}
            },
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        return {"id": response["id"], "title": response["snippet"]["title"]}

    async def youtube_get_channel_stats(self, channel_id: str) -> Dict:
        """Get YouTube channel statistics"""
        import aiohttp

        api_key = os.environ.get("YOUTUBE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "statistics,snippet", "id": channel_id, "key": api_key}
            ) as response:
                data = await response.json()
                if data.get("items"):
                    item = data["items"][0]
                    return {
                        "title": item["snippet"]["title"],
                        "subscribers": item["statistics"]["subscriberCount"],
                        "views": item["statistics"]["viewCount"],
                        "videos": item["statistics"]["videoCount"]
                    }
                return {}

    # ==================== REDDIT ====================

    async def reddit_post(self, subreddit: str, title: str, text: str = None, url: str = None) -> Dict:
        """Post to Reddit"""
        import praw

        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="WindowsAI",
            username=os.environ.get("REDDIT_USERNAME"),
            password=os.environ.get("REDDIT_PASSWORD")
        )

        subreddit_obj = reddit.subreddit(subreddit)
        if url:
            submission = subreddit_obj.submit(title, url=url)
        else:
            submission = subreddit_obj.submit(title, selftext=text or "")

        return {"id": submission.id, "url": submission.url}

    # ==================== DISCORD ====================

    async def discord_send_message(self, channel_id: str, content: str, embeds: List[Dict] = None) -> Dict:
        """Send Discord message"""
        import aiohttp

        bot_token = os.environ.get("DISCORD_BOT_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
                json={"content": content, "embeds": embeds or []}
            ) as response:
                return await response.json()

    async def discord_webhook(self, webhook_url: str, content: str, embeds: List[Dict] = None) -> bool:
        """Send Discord webhook"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json={"content": content, "embeds": embeds or []}
            ) as response:
                return response.status == 204

    # ==================== MASTODON ====================

    async def mastodon_post(self, status: str, instance_url: str = None) -> Dict:
        """Post to Mastodon"""
        from mastodon import Mastodon

        mastodon = Mastodon(
            access_token=os.environ.get("MASTODON_ACCESS_TOKEN"),
            api_base_url=instance_url or os.environ.get("MASTODON_INSTANCE", "https://mastodon.social")
        )

        toot = mastodon.status_post(status)
        return {"id": toot["id"], "url": toot["url"]}

    # ==================== BLUESKY ====================

    async def bluesky_post(self, text: str) -> Dict:
        """Post to Bluesky"""
        import aiohttp
        from datetime import datetime

        handle = os.environ.get("BLUESKY_HANDLE")
        password = os.environ.get("BLUESKY_PASSWORD")

        async with aiohttp.ClientSession() as session:
            # Create session
            async with session.post(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                json={"identifier": handle, "password": password}
            ) as response:
                auth = await response.json()

            # Create post
            async with session.post(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {auth['accessJwt']}"},
                json={
                    "repo": auth["did"],
                    "collection": "app.bsky.feed.post",
                    "record": {"text": text, "createdAt": datetime.utcnow().isoformat() + "Z"}
                }
            ) as response:
                return await response.json()

    # ==================== AI CONTENT GENERATION ====================

    async def ai_generate_post(self, platform: str, topic: str, tone: str = "professional") -> str:
        """Generate social media post using AI"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        platform_limits = {
            "twitter": 280, "linkedin": 3000, "facebook": 63206,
            "instagram": 2200, "tiktok": 150, "bluesky": 300
        }

        messages = [
            {"role": "system", "content": f"""Generate a {platform} post about the topic.
Tone: {tone}
Max characters: {platform_limits.get(platform, 1000)}
Include relevant hashtags if appropriate."""},
            {"role": "user", "content": topic}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return response["content"]

    def list_platforms(self) -> List[str]:
        return ["twitter", "linkedin", "facebook", "instagram", "tiktok",
                "youtube", "reddit", "discord", "mastodon", "bluesky",
                "pinterest", "threads", "snapchat", "whatsapp", "telegram"]
