"""
Reddit Social Media Plugin
Supports posting, commenting, and subreddit monitoring
"""

from typing import Dict, Any, Optional, List
import os
import time


class RedditPlugin:
    """Plugin for Reddit API integration"""
    
    name = "reddit"
    version = "1.0.0"
    description = "Integration with Reddit API for posting, commenting, and subreddit monitoring"
    author = "Windows AI Team"
    
    def __init__(self):
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.user_agent: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.reddit = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Reddit plugin"""
        try:
            import praw
            
            # Get credentials from config or environment
            self.client_id = (
                config.get("client_id") if config 
                else os.getenv("REDDIT_CLIENT_ID")
            )
            self.client_secret = (
                config.get("client_secret") if config 
                else os.getenv("REDDIT_CLIENT_SECRET")
            )
            self.user_agent = (
                config.get("user_agent") if config 
                else os.getenv("REDDIT_USER_AGENT") or "WindowsAI/1.0"
            )
            self.username = (
                config.get("username") if config 
                else os.getenv("REDDIT_USERNAME")
            )
            self.password = (
                config.get("password") if config 
                else os.getenv("REDDIT_PASSWORD")
            )
            
            if not all([self.client_id, self.client_secret]):
                return False
                
            # Initialize PRAW client
            if self.username and self.password:
                # Authenticated user
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                    username=self.username,
                    password=self.password
                )
            else:
                # Read-only client
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
            
            # Test connection
            try:
                self.reddit.read_only
                self._initialized = True
                return True
            except Exception:
                return False
            
        except ImportError:
            print("praw package not installed. Install with: pip install praw")
            return False
        except Exception as e:
            print(f"Error initializing Reddit plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Reddit action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Reddit API credentials."}
        
        try:
            if action == "post":
                return self._post_submission(params)
            elif action == "comment":
                return self._post_comment(params)
            elif action == "monitor_subreddit":
                return self._monitor_subreddit(params)
            elif action == "get_posts":
                return self._get_posts(params)
            elif action == "get_comments":
                return self._get_comments(params)
            elif action == "search":
                return self._search(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _post_submission(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post a submission to a subreddit"""
        subreddit = params.get("subreddit", "")
        title = params.get("title", "")
        text = params.get("text", "")
        url = params.get("url", "")
        flair_id = params.get("flair_id")
        nsfw = params.get("nsfw", False)
        spoiler = params.get("spoiler", False)
        
        if not subreddit or not title:
            return {"error": "subreddit and title are required"}
        
        if not text and not url:
            return {"error": "Either text or url is required"}
        
        try:
            subreddit_obj = self.reddit.subreddit(subreddit)
            
            if url:
                submission = subreddit_obj.submit(
                    title=title,
                    url=url,
                    flair_id=flair_id,
                    nsfw=nsfw,
                    spoiler=spoiler
                )
            else:
                submission = subreddit_obj.submit(
                    title=title,
                    selftext=text,
                    flair_id=flair_id,
                    nsfw=nsfw,
                    spoiler=spoiler
                )
            
            return {
                "success": True,
                "post_id": submission.id,
                "url": f"https://reddit.com{submission.permalink}",
                "title": title,
                "subreddit": subreddit
            }
        except Exception as e:
            return {"error": f"Failed to post submission: {str(e)}"}
    
    def _post_comment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post a comment on a submission or reply to another comment"""
        post_id = params.get("post_id", "")
        comment_id = params.get("comment_id", "")
        text = params.get("text", "")
        
        if not text:
            return {"error": "Comment text is required"}
        
        if not post_id and not comment_id:
            return {"error": "Either post_id or comment_id is required"}
        
        try:
            if post_id:
                submission = self.reddit.submission(id=post_id)
                comment = submission.reply(text)
            else:
                comment_obj = self.reddit.comment(id=comment_id)
                comment = comment_obj.reply(text)
            
            return {
                "success": True,
                "comment_id": comment.id,
                "url": f"https://reddit.com{comment.permalink}",
                "text": text
            }
        except Exception as e:
            return {"error": f"Failed to post comment: {str(e)}"}
    
    def _monitor_subreddit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor a subreddit for new posts"""
        subreddit = params.get("subreddit", "")
        sort = params.get("sort", "new")  # new, hot, top, rising
        time_filter = params.get("time_filter", "hour")  # hour, day, week, month, year, all
        limit = params.get("limit", 25)
        keywords = params.get("keywords", [])
        
        if not subreddit:
            return {"error": "subreddit is required"}
        
        if limit > 100:
            limit = 100  # API limit
        
        try:
            subreddit_obj = self.reddit.subreddit(subreddit)
            posts = []
            
            if sort == "new":
                submissions = subreddit_obj.new(limit=limit)
            elif sort == "hot":
                submissions = subreddit_obj.hot(limit=limit)
            elif sort == "top":
                submissions = subreddit_obj.top(time_filter=time_filter, limit=limit)
            elif sort == "rising":
                submissions = subreddit_obj.rising(limit=limit)
            else:
                submissions = subreddit_obj.new(limit=limit)
            
            for submission in submissions:
                # Filter by keywords if provided
                if keywords:
                    text_to_check = f"{submission.title.lower()} {submission.selftext.lower()}"
                    if not any(keyword.lower() in text_to_check for keyword in keywords):
                        continue
                
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "url": f"https://reddit.com{submission.permalink}",
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "created_at": submission.created_utc,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "subreddit": str(submission.subreddit),
                    "is_self": submission.is_self,
                    "selftext": submission.selftext if submission.is_self else None,
                    "url_overridden": submission.url if not submission.is_self else None,
                    "nsfw": submission.over_18,
                    "spoiler": submission.spoiler
                })
            
            return {
                "posts": posts,
                "count": len(posts),
                "subreddit": subreddit,
                "sort": sort,
                "time_filter": time_filter
            }
        except Exception as e:
            return {"error": f"Failed to monitor subreddit: {str(e)}"}
    
    def _get_posts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get posts from multiple subreddits"""
        subreddits = params.get("subreddits", [])
        sort = params.get("sort", "hot")
        limit = params.get("limit", 25)
        
        if not subreddits:
            return {"error": "subreddits list is required"}
        
        if limit > 100:
            limit = 100
        
        try:
            subreddit_str = "+".join(subreddits)
            subreddit_obj = self.reddit.subreddit(subreddit_str)
            posts = []
            
            if sort == "new":
                submissions = subreddit_obj.new(limit=limit)
            elif sort == "hot":
                submissions = subreddit_obj.hot(limit=limit)
            elif sort == "top":
                submissions = subreddit_obj.top(limit=limit)
            elif sort == "rising":
                submissions = subreddit_obj.rising(limit=limit)
            else:
                submissions = subreddit_obj.hot(limit=limit)
            
            for submission in submissions:
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "url": f"https://reddit.com{submission.permalink}",
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "created_at": submission.created_utc,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "subreddit": str(submission.subreddit),
                    "is_self": submission.is_self,
                    "selftext": submission.selftext if submission.is_self else None,
                    "url_overridden": submission.url if not submission.is_self else None,
                    "nsfw": submission.over_18,
                    "spoiler": submission.spoiler
                })
            
            return {
                "posts": posts,
                "count": len(posts),
                "subreddits": subreddits,
                "sort": sort
            }
        except Exception as e:
            return {"error": f"Failed to get posts: {str(e)}"}
    
    def _get_comments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comments from a post"""
        post_id = params.get("post_id", "")
        sort = params.get("sort", "best")  # best, top, new, controversial, old
        limit = params.get("limit", 50)
        
        if not post_id:
            return {"error": "post_id is required"}
        
        if limit > 100:
            limit = 100
        
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comment_sort = sort
            comments = []
            
            submission.comments.replace_more(limit=0)  # Remove "more comments" placeholders
            
            for comment in submission.comments.list()[:limit]:
                comments.append({
                    "id": comment.id,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body,
                    "score": comment.score,
                    "created_at": comment.created_utc,
                    "depth": comment.depth,
                    "is_submitter": comment.is_submitter,
                    "replies": len(comment.replies) if hasattr(comment, 'replies') else 0,
                    "url": f"https://reddit.com{comment.permalink}"
                })
            
            return {
                "comments": comments,
                "count": len(comments),
                "post_id": post_id,
                "post_title": submission.title,
                "sort": sort
            }
        except Exception as e:
            return {"error": f"Failed to get comments: {str(e)}"}
    
    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Reddit"""
        query = params.get("query", "")
        subreddit = params.get("subreddit", "")
        sort = params.get("sort", "relevance")  # relevance, hot, top, new, comments
        time_filter = params.get("time_filter", "all")
        limit = params.get("limit", 25)
        
        if not query:
            return {"error": "query is required"}
        
        if limit > 100:
            limit = 100
        
        try:
            if subreddit:
                subreddit_obj = self.reddit.subreddit(subreddit)
                results = subreddit_obj.search(
                    query=query,
                    sort=sort,
                    time_filter=time_filter,
                    limit=limit
                )
            else:
                results = self.reddit.subreddit("all").search(
                    query=query,
                    sort=sort,
                    time_filter=time_filter,
                    limit=limit
                )
            
            posts = []
            for submission in results:
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "url": f"https://reddit.com{submission.permalink}",
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "created_at": submission.created_utc,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "subreddit": str(submission.subreddit),
                    "is_self": submission.is_self,
                    "selftext": submission.selftext if submission.is_self else None,
                    "url_overridden": submission.url if not submission.is_self else None,
                    "nsfw": submission.over_18,
                    "spoiler": submission.spoiler
                })
            
            return {
                "posts": posts,
                "count": len(posts),
                "query": query,
                "subreddit": subreddit if subreddit else "all",
                "sort": sort,
                "time_filter": time_filter
            }
        except Exception as e:
            return {"error": f"Failed to search: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        self.reddit = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = RedditPlugin
PLUGIN_NAME = "reddit"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Reddit API for posting, commenting, and subreddit monitoring"
PLUGIN_ACTIONS = [
    "post", "comment", "monitor_subreddit", "get_posts", 
    "get_comments", "search"
]