"""
Knowledge Graph Manager - GraphRAG and Graph Databases
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class KnowledgeGraphManager:
    """GraphRAG and knowledge graph operations"""

    def __init__(self):
        self._initialized = False
        self._driver = None

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True
        logger.info("Knowledge Graph Manager initialized")

    async def connect_neo4j(self, uri: str = None, user: str = None, password: str = None):
        """Connect to Neo4j"""
        from neo4j import AsyncGraphDatabase

        uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = user or os.environ.get("NEO4J_USER", "neo4j")
        password = password or os.environ.get("NEO4J_PASSWORD")

        self._driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def create_node(self, label: str, properties: Dict[str, Any]) -> Dict:
        """Create a node"""
        async with self._driver.session() as session:
            query = f"CREATE (n:{label} $props) RETURN n"
            result = await session.run(query, props=properties)
            record = await result.single()
            return dict(record["n"])

    async def create_relationship(
        self,
        from_label: str,
        from_props: Dict,
        rel_type: str,
        to_label: str,
        to_props: Dict
    ) -> bool:
        """Create a relationship between nodes"""
        async with self._driver.session() as session:
            query = f"""
            MATCH (a:{from_label}), (b:{to_label})
            WHERE a.id = $from_id AND b.id = $to_id
            CREATE (a)-[r:{rel_type}]->(b)
            RETURN r
            """
            await session.run(query, from_id=from_props.get("id"), to_id=to_props.get("id"))
            return True

    async def query(self, cypher: str, params: Dict = None) -> List[Dict]:
        """Execute Cypher query"""
        async with self._driver.session() as session:
            result = await session.run(cypher, params or {})
            records = await result.data()
            return records

    async def text_to_cypher(self, question: str, schema: str = None, llm_provider: str = "openai") -> str:
        """Convert natural language to Cypher query"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are a Neo4j Cypher expert. Convert natural language to Cypher queries.
Schema: {schema or 'Unknown - generate a reasonable query'}
Return ONLY the Cypher query."""},
            {"role": "user", "content": question}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)
        return response["content"].strip()

    async def build_knowledge_graph_from_text(
        self,
        text: str,
        llm_provider: str = "openai"
    ) -> Dict[str, Any]:
        """Extract entities and relationships from text to build knowledge graph"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
        import json

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Extract entities and relationships from the text.
Return JSON with format:
{
    "entities": [{"id": "...", "label": "Person|Organization|Concept|...", "properties": {...}}],
    "relationships": [{"from": "id1", "to": "id2", "type": "RELATES_TO|WORKS_FOR|..."}]
}"""},
            {"role": "user", "content": text}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        try:
            graph_data = json.loads(response["content"])

            # Create nodes
            for entity in graph_data.get("entities", []):
                await self.create_node(entity["label"], entity.get("properties", {}))

            # Create relationships
            for rel in graph_data.get("relationships", []):
                await self.query(f"""
                    MATCH (a), (b)
                    WHERE a.id = $from_id AND b.id = $to_id
                    CREATE (a)-[:{rel['type']}]->(b)
                """, {"from_id": rel["from"], "to_id": rel["to"]})

            return graph_data
        except json.JSONDecodeError:
            return {"raw_response": response["content"]}

    async def graphrag_query(
        self,
        question: str,
        context_depth: int = 2,
        llm_provider: str = "openai"
    ) -> str:
        """GraphRAG: Answer questions using knowledge graph context"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        # First, extract entities from question
        ai = AIProvidersManager()
        await ai.initialize()

        # Get relevant context from graph
        cypher = await self.text_to_cypher(
            f"Find entities and relationships related to: {question}",
            llm_provider=llm_provider
        )

        try:
            context = await self.query(cypher)
        except Exception:
            context = []

        # Generate answer with context
        messages = [
            {"role": "system", "content": f"""Answer the question using the provided knowledge graph context.
Context from knowledge graph: {context}"""},
            {"role": "user", "content": question}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)
        return response["content"]

    async def close(self):
        """Close database connection"""
        if self._driver:
            await self._driver.close()
