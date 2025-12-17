"""
Search Toolkit - Text processing and query analysis utilities
Provides text preprocessing, query parsing, relevance scoring, and result formatting.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from functools import wraps

logger = logging.getLogger(__name__)


def async_timer(func):
    """
    Decorator to measure execution time of async functions.
    
    Args:
        func: Async function to measure
    
    Returns:
        Wrapped async function with timing
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    return wrapper


@dataclass
class TokenizedQuery:
    """Parsed and tokenized search query."""
    original: str
    tokens: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedResult:
    """Search result with processing and formatting."""
    id: str
    title: str
    snippet: str
    relevance_score: float
    relevance_details: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class SearchToolkit:
    """
    Search toolkit for text processing and query analysis.
    
    Provides utilities for:
    - Text preprocessing (normalization, cleaning)
    - Query tokenization and parsing
    - Entity and filter extraction
    - Relevance scoring
    - Result formatting with snippets
    - Performance monitoring
    
    Example:
        toolkit = SearchToolkit(config)
        await toolkit.setup()
        tokenized = await toolkit.parse_query("search text")
        score = await toolkit.calculate_relevance(tokenized.tokens, result_text)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the search toolkit.
        
        Args:
            config: Configuration dictionary with:
                - stopwords_enabled: Enable stopword filtering (default: True)
                - min_token_length: Minimum token length (default: 2)
                - max_snippet_length: Max snippet length in chars (default: 200)
                - lemmatization_enabled: Enable lemmatization (default: False)
        """
        self.config = config or {}
        self._initialized = False
        self.stopwords_enabled = self.config.get("stopwords_enabled", True)
        self.min_token_length = self.config.get("min_token_length", 2)
        self.max_snippet_length = self.config.get("max_snippet_length", 200)
        self.lemmatization_enabled = self.config.get("lemmatization_enabled", False)
        
        self.stopwords: Set[str] = set()
        
        logger.debug(f"SearchToolkit initialized with stopwords_enabled={self.stopwords_enabled}")
    
    async def setup(self) -> bool:
        """
        Set up the toolkit and load resources.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if self._initialized:
            logger.warning("SearchToolkit already initialized")
            return True
        
        try:
            logger.info("Starting SearchToolkit setup")
            
            # Load stopwords
            self.stopwords = self._load_stopwords()
            logger.debug(f"Loaded {len(self.stopwords)} stopwords")
            
            self._initialized = True
            logger.info("SearchToolkit setup complete")
            return True
            
        except Exception as e:
            logger.error(f"SearchToolkit setup failed: {e}", exc_info=True)
            self._initialized = False
            return False
    
    def _load_stopwords(self) -> Set[str]:
        """
        Load English stopwords.
        
        Returns:
            Set of common English stopwords
        """
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through", "during",
            "is", "are", "am", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can",
            "i", "you", "he", "she", "it", "we", "they", "what", "which", "who",
            "this", "that", "these", "those", "i", "you", "your", "his", "her",
            "my", "our", "their", "if", "because", "as", "while", "although"
        }
        return stopwords
    
    @async_timer
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute toolkit operations based on provided parameters.
        
        Args:
            **kwargs: Operation parameters including:
                - operation: Type of operation (preprocess/parse_query/tokenize)
                - text: Text to process
                - query: Query text to parse
                - results: Results to format
        
        Returns:
            Dictionary with operation results
        
        Raises:
            ValueError: If required parameters missing
        """
        if not self._initialized:
            raise RuntimeError("SearchToolkit not initialized. Call setup() first.")
        
        operation = kwargs.get("operation", "preprocess")
        
        try:
            if operation == "preprocess":
                text = kwargs.get("text", "")
                result = await self.preprocess_text(text)
                return {"status": "success", "result": result}
                
            elif operation == "parse_query":
                query = kwargs.get("query", "")
                result = await self.parse_query(query)
                return {"status": "success", "result": result}
                
            elif operation == "tokenize":
                text = kwargs.get("text", "")
                result = await self.tokenize(text)
                return {"status": "success", "result": result}
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"Toolkit operation '{operation}' failed: {e}", exc_info=True)
            raise
    
    @async_timer
    async def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by normalizing and cleaning.
        
        Performs:
        - Lowercase conversion
        - Special character removal
        - Whitespace normalization
        - Extra space removal
        
        Args:
            text: Text to preprocess
        
        Returns:
            Preprocessed text
        """
        logger.debug(f"Preprocessing text of length {len(text)}")
        
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        logger.debug("Applied lowercase")
        
        # Remove special characters (keep alphanumeric and spaces)
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        logger.debug("Removed special characters")
        
        # Normalize whitespace (multiple spaces to single space)
        text = re.sub(r"\s+", " ", text)
        logger.debug("Normalized whitespace")
        
        # Strip leading/trailing spaces
        text = text.strip()
        
        logger.debug(f"Preprocessing complete, result length: {len(text)}")
        return text
    
    @async_timer
    async def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Applies:
        - Whitespace splitting
        - Minimum length filtering
        - Stopword filtering (if enabled)
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        logger.debug(f"Tokenizing text of length {len(text)}")
        
        # Preprocess text first
        text = await self.preprocess_text(text)
        
        # Split into tokens
        tokens = text.split()
        logger.debug(f"Split into {len(tokens)} raw tokens")
        
        # Filter by minimum length
        tokens = [t for t in tokens if len(t) >= self.min_token_length]
        logger.debug(f"Filtered to {len(tokens)} tokens by min_length={self.min_token_length}")
        
        # Filter stopwords
        if self.stopwords_enabled:
            original_count = len(tokens)
            tokens = [t for t in tokens if t not in self.stopwords]
            logger.debug(f"Filtered {original_count - len(tokens)} stopwords, {len(tokens)} remaining")
        
        logger.debug(f"Tokenization complete: {len(tokens)} tokens")
        return tokens
    
    @async_timer
    async def parse_query(self, query: str) -> TokenizedQuery:
        """
        Parse search query into components.
        
        Extracts:
        - Tokens
        - Keywords
        - Entities (emails, URLs, proper nouns)
        - Filters (filter:value pairs)
        
        Args:
            query: Query text to parse
        
        Returns:
            TokenizedQuery object with parsed components
        """
        logger.info(f"Parsing query: '{query}'")
        
        if not query:
            logger.warning("Empty query provided")
            return TokenizedQuery(original=query)
        
        try:
            # Tokenize the query
            tokens = await self.tokenize(query)
            logger.debug(f"Tokenized to {len(tokens)} tokens")
            
            # Extract entities
            entities = await self._extract_entities(query)
            logger.debug(f"Extracted {len(entities)} entities")
            
            # Extract filters
            filters = await self._extract_filters(query)
            logger.debug(f"Extracted {len(filters)} filters")
            
            # Keywords are high-value tokens (not stopwords, good length)
            keywords = [t for t in tokens if len(t) > 3]
            logger.debug(f"Identified {len(keywords)} keywords")
            
            result = TokenizedQuery(
                original=query,
                tokens=tokens,
                keywords=keywords,
                entities=entities,
                filters=filters
            )
            
            logger.info(f"Query parse complete: {len(tokens)} tokens, {len(keywords)} keywords, {len(entities)} entities")
            return result
            
        except Exception as e:
            logger.error(f"Query parsing failed: {e}", exc_info=True)
            raise
    
    async def _extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities from text.
        
        Identifies:
        - Email addresses
        - URLs
        - Proper nouns (capitalized words)
        
        Args:
            text: Text to analyze
        
        Returns:
            List of extracted entities (max 10)
        """
        logger.debug("Extracting entities from text")
        
        entities = []
        
        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        entities.extend(emails)
        if emails:
            logger.debug(f"Found {len(emails)} emails: {emails[:3]}")
        
        # URL pattern
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, text)
        entities.extend(urls)
        if urls:
            logger.debug(f"Found {len(urls)} URLs")
        
        # Proper nouns (capitalized words)
        proper_noun_pattern = r"\b[A-Z][a-z]*\b"
        proper_nouns = re.findall(proper_noun_pattern, text)
        # Filter out common words that happen to be capitalized
        proper_nouns = [pn for pn in proper_nouns if len(pn) > 2]
        entities.extend(proper_nouns[:5])
        if proper_nouns:
            logger.debug(f"Found {len(proper_nouns)} proper nouns")
        
        # Limit to 10 entities
        entities = entities[:10]
        logger.debug(f"Total entities extracted: {len(entities)}")
        
        return entities
    
    async def _extract_filters(self, text: str) -> Dict[str, Any]:
        """
        Extract filter specifications from query.
        
        Looks for patterns like:
        - filter:value
        - type:email
        - date:2024
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary of filter:value pairs
        """
        logger.debug("Extracting filters from text")
        
        filters = {}
        filter_pattern = r"(\w+):(\w+)"
        matches = re.findall(filter_pattern, text)
        
        for key, value in matches:
            filters[key.lower()] = value.lower()
            logger.debug(f"Extracted filter: {key}={value}")
        
        logger.debug(f"Total filters extracted: {len(filters)}")
        return filters
    
    @async_timer
    async def calculate_relevance(
        self,
        query_tokens: List[str],
        result_text: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate relevance score between query and result text.
        
        Scoring:
        - Token match: 60% weight (number of query tokens found)
        - Position: 40% weight (proximity of matches to start)
        
        Args:
            query_tokens: Query tokens from parse_query
            result_text: Result text to score
        
        Returns:
            Tuple of (relevance_score, details_dict)
        """
        logger.debug(f"Calculating relevance for {len(query_tokens)} tokens against {len(result_text)} chars")
        
        if not query_tokens or not result_text:
            logger.debug("Empty tokens or result text, returning zero score")
            return 0.0, {"token_matches": 0, "position_score": 0}
        
        result_lower = result_text.lower()
        
        # Token matching (60% weight)
        token_matches = 0
        for token in query_tokens:
            if token in result_lower:
                token_matches += 1
        
        token_score = (token_matches / len(query_tokens)) * 0.6 if query_tokens else 0
        logger.debug(f"Token matches: {token_matches}/{len(query_tokens)}, score: {token_score:.2f}")
        
        # Position scoring (40% weight)
        # Score based on how early matches appear
        position_score = 0
        for token in query_tokens:
            pos = result_lower.find(token)
            if pos >= 0:
                # Earlier matches = higher score
                proximity = 1 - (pos / len(result_text))
                position_score += proximity
        
        position_score = (position_score / len(query_tokens)) * 0.4 if query_tokens else 0
        logger.debug(f"Position score: {position_score:.2f}")
        
        # Final score
        relevance = token_score + position_score
        relevance = min(1.0, max(0.0, relevance))  # Clamp to 0-1
        
        details = {
            "token_matches": token_matches,
            "position_score": position_score,
            "token_score": token_score,
            "total_tokens": len(query_tokens)
        }
        
        logger.debug(f"Relevance score: {relevance:.2f}")
        return relevance, details
    
    @async_timer
    async def format_results(
        self,
        results: List[Dict[str, Any]],
        query_tokens: List[str]
    ) -> List[ProcessedResult]:
        """
        Format and enhance search results with snippets and relevance.
        
        Args:
            results: List of raw result dictionaries with id, title, content, source
            query_tokens: Query tokens for snippet generation
        
        Returns:
            List of ProcessedResult objects
        """
        logger.info(f"Formatting {len(results)} results")
        
        processed = []
        
        for i, result in enumerate(results):
            try:
                # Extract fields
                result_id = result.get("id", f"result-{i}")
                title = result.get("title", "")
                content = result.get("content", "")
                source = result.get("source", "")
                metadata = result.get("metadata", {})
                
                # Calculate relevance
                relevance, details = await self.calculate_relevance(query_tokens, content)
                
                # Generate snippet
                snippet = await self._generate_snippet(content, query_tokens)
                
                # Create processed result
                processed_result = ProcessedResult(
                    id=result_id,
                    title=title,
                    snippet=snippet,
                    relevance_score=relevance,
                    relevance_details=details,
                    source=source,
                    metadata=metadata
                )
                
                processed.append(processed_result)
                logger.debug(f"Formatted result {result_id}: score={relevance:.2f}")
                
            except Exception as e:
                logger.error(f"Error formatting result {i}: {e}")
                continue
        
        logger.info(f"Formatting complete: {len(processed)} results processed")
        return processed
    
    async def _generate_snippet(
        self,
        text: str,
        query_tokens: List[str],
        context_window: int = 50
    ) -> str:
        """
        Generate snippet around query tokens.
        
        Args:
            text: Full text to extract from
            query_tokens: Tokens to search for
            context_window: Characters around match (default: 50)
        
        Returns:
            Snippet text with context
        """
        logger.debug(f"Generating snippet from {len(text)} chars with {context_window} context window")
        
        if not text:
            return ""
        
        text_lower = text.lower()
        
        # Find first query token in text
        first_match_pos = -1
        for token in query_tokens:
            pos = text_lower.find(token)
            if pos >= 0:
                first_match_pos = pos
                break
        
        if first_match_pos < 0:
            # No match found, return first part of text
            snippet = text[:self.max_snippet_length]
            logger.debug(f"No match found, returning first {len(snippet)} chars")
            return snippet
        
        # Extract context around first match
        start = max(0, first_match_pos - context_window)
        end = min(len(text), first_match_pos + context_window + 50)
        
        snippet = text[start:end].strip()
        
        # Truncate to max length
        if len(snippet) > self.max_snippet_length:
            snippet = snippet[:self.max_snippet_length - 3] + "..."
        
        logger.debug(f"Generated snippet: {len(snippet)} chars")
        return snippet
    
    async def cleanup(self) -> None:
        """
        Clean up toolkit resources.
        """
        logger.info("SearchToolkit cleanup starting")
        
        self._initialized = False
        self.stopwords.clear()
        
        logger.info("SearchToolkit cleanup complete")
