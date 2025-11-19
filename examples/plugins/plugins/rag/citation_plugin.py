"""
Citation Plugin
Track and attribute sources in RAG responses
"""

from typing import Dict, Any, Optional, List
import hashlib
from datetime import datetime


class CitationPlugin:
    """Plugin for citation and source attribution in RAG"""

    name = "citation"
    version = "1.0.0"
    description = "Track and cite sources used in generated responses"
    author = "Windows AI Team"

    def __init__(self):
        self.sources = {}
        self.citations = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Citation plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Citation plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Citation action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_source":
                return self._add_source(params)
            elif action == "cite":
                return self._cite(params)
            elif action == "format_citations":
                return self._format_citations(params)
            elif action == "inline_citations":
                return self._inline_citations(params)
            elif action == "verify_citations":
                return self._verify_citations(params)
            elif action == "get_bibliography":
                return self._get_bibliography()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a source document to the citation database"""
        document = params.get("document", "")
        metadata = params.get("metadata", {})

        # Generate unique source ID
        source_id = hashlib.md5(document.encode()).hexdigest()[:12]

        source = {
            "id": source_id,
            "document": document,
            "metadata": metadata,
            "added_at": datetime.now().isoformat(),
            "citation_count": 0
        }

        self.sources[source_id] = source

        return {
            "success": True,
            "source_id": source_id,
            "metadata": metadata
        }

    def _cite(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a citation for a specific claim"""
        claim = params.get("claim", "")
        source_ids = params.get("source_ids", [])
        citation_style = params.get("style", "numeric")  # numeric, author-year, footnote

        if not isinstance(source_ids, list):
            source_ids = [source_ids]

        # Verify all sources exist
        for sid in source_ids:
            if sid not in self.sources:
                return {"success": False, "error": f"Source {sid} not found"}

        # Generate citation
        citation_id = len(self.citations) + 1

        citation = {
            "id": citation_id,
            "claim": claim,
            "source_ids": source_ids,
            "style": citation_style,
            "created_at": datetime.now().isoformat()
        }

        # Update citation counts
        for sid in source_ids:
            self.sources[sid]["citation_count"] += 1

        self.citations.append(citation)

        # Format citation based on style
        if citation_style == "numeric":
            formatted = f"[{citation_id}]"
        elif citation_style == "author-year":
            authors = []
            for sid in source_ids:
                author = self.sources[sid]["metadata"].get("author", "Unknown")
                year = self.sources[sid]["metadata"].get("year", "n.d.")
                authors.append(f"{author}, {year}")
            formatted = f"({'; '.join(authors)})"
        elif citation_style == "footnote":
            formatted = f"^{citation_id}"
        else:
            formatted = f"[{citation_id}]"

        return {
            "success": True,
            "citation_id": citation_id,
            "formatted": formatted,
            "sources": len(source_ids)
        }

    def _format_citations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Format all citations in a specific style"""
        style = params.get("style", "apa")  # apa, mla, chicago, ieee

        formatted_citations = []

        for citation in self.citations:
            sources = []
            for sid in citation["source_ids"]:
                if sid not in self.sources:
                    continue

                source = self.sources[sid]
                metadata = source["metadata"]

                if style == "apa":
                    # APA: Author, A. A. (Year). Title. Source.
                    author = metadata.get("author", "Unknown")
                    year = metadata.get("year", "n.d.")
                    title = metadata.get("title", "Untitled")
                    source_name = metadata.get("source", "Unknown source")
                    formatted = f"{author} ({year}). {title}. {source_name}."

                elif style == "mla":
                    # MLA: Author. "Title." Source, Year.
                    author = metadata.get("author", "Unknown")
                    title = metadata.get("title", "Untitled")
                    source_name = metadata.get("source", "Unknown source")
                    year = metadata.get("year", "n.d.")
                    formatted = f'{author}. "{title}." {source_name}, {year}.'

                elif style == "chicago":
                    # Chicago: Author. Title. Source, Year.
                    author = metadata.get("author", "Unknown")
                    title = metadata.get("title", "Untitled")
                    source_name = metadata.get("source", "Unknown source")
                    year = metadata.get("year", "n.d.")
                    formatted = f"{author}. {title}. {source_name}, {year}."

                elif style == "ieee":
                    # IEEE: [#] Author, "Title," Source, Year.
                    author = metadata.get("author", "Unknown")
                    title = metadata.get("title", "Untitled")
                    source_name = metadata.get("source", "Unknown source")
                    year = metadata.get("year", "n.d.")
                    formatted = f'[{citation["id"]}] {author}, "{title}," {source_name}, {year}.'

                else:
                    formatted = f"Source {sid}"

                sources.append(formatted)

            formatted_citations.append({
                "citation_id": citation["id"],
                "claim": citation["claim"],
                "formatted_sources": sources
            })

        return {
            "success": True,
            "citations": formatted_citations,
            "count": len(formatted_citations),
            "style": style
        }

    def _inline_citations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add inline citations to text"""
        text = params.get("text", "")
        claims_with_sources = params.get("claims", [])
        # claims format: [{"text": "claim text", "source_ids": ["src1", "src2"]}]

        cited_text = text

        for claim_info in claims_with_sources:
            claim_text = claim_info.get("text", "")
            source_ids = claim_info.get("source_ids", [])

            if claim_text not in text:
                continue

            # Create citation
            citation_result = self._cite({
                "claim": claim_text,
                "source_ids": source_ids,
                "style": params.get("style", "numeric")
            })

            if citation_result["success"]:
                citation_mark = citation_result["formatted"]
                # Insert citation after claim
                cited_text = cited_text.replace(
                    claim_text,
                    f"{claim_text}{citation_mark}",
                    1  # Replace only first occurrence
                )

        return {
            "success": True,
            "original_text": text,
            "cited_text": cited_text,
            "citations_added": len(claims_with_sources)
        }

    def _verify_citations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that citations accurately represent sources"""
        claims = params.get("claims", [])
        # claims format: [{"claim": "text", "source_id": "src1"}]

        verified = []

        for claim_info in claims:
            claim = claim_info.get("claim", "")
            source_id = claim_info.get("source_id", "")

            if source_id not in self.sources:
                verified.append({
                    "claim": claim,
                    "source_id": source_id,
                    "verified": False,
                    "reason": "Source not found"
                })
                continue

            source = self.sources[source_id]
            source_text = source["document"].lower()
            claim_lower = claim.lower()

            # Simple verification: check if claim terms appear in source
            claim_terms = set(claim_lower.split())
            source_terms = set(source_text.split())
            overlap = len(claim_terms & source_terms) / len(claim_terms) if claim_terms else 0

            # Consider verified if >70% of claim terms appear in source
            is_verified = overlap > 0.7

            verified.append({
                "claim": claim,
                "source_id": source_id,
                "verified": is_verified,
                "confidence": overlap,
                "reason": "High term overlap" if is_verified else "Low term overlap"
            })

        return {
            "success": True,
            "verifications": verified,
            "total": len(verified),
            "verified_count": sum(1 for v in verified if v["verified"])
        }

    def _get_bibliography(self) -> Dict[str, Any]:
        """Get formatted bibliography of all sources"""
        bibliography = []

        for source_id, source in self.sources.items():
            metadata = source["metadata"]

            entry = {
                "source_id": source_id,
                "metadata": metadata,
                "citation_count": source["citation_count"],
                "preview": source["document"][:200] + "..." if len(source["document"]) > 200 else source["document"]
            }

            bibliography.append(entry)

        # Sort by citation count (most cited first)
        bibliography.sort(key=lambda x: x["citation_count"], reverse=True)

        return {
            "success": True,
            "bibliography": bibliography,
            "total_sources": len(bibliography),
            "total_citations": len(self.citations)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.sources = {}
        self.citations = []
        return True
