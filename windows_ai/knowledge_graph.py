"""Knowledge Graph Builder"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    properties: Dict[str, Any]

@dataclass
class Relation:
    relation_id: str
    source: str
    target: str
    relation_type: str

class KnowledgeGraphBuilder:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.entities: List[Entity] = []
        self.relations: List[Relation] = []
        logger.info("Knowledge Graph Builder initialized")

    def add_entity(self, name: str, entity_type: str, properties: Dict) -> Entity:
        import uuid
        entity = Entity(str(uuid.uuid4()), name, entity_type, properties)
        self.entities.append(entity)
        return entity

    def add_relation(self, source: str, target: str, rel_type: str) -> Relation:
        import uuid
        rel = Relation(str(uuid.uuid4()), source, target, rel_type)
        self.relations.append(rel)
        return rel

_kg_builder: Optional[KnowledgeGraphBuilder] = None
def get_kg_builder() -> Optional[KnowledgeGraphBuilder]: return _kg_builder
def initialize_kg_builder(data_dir) -> KnowledgeGraphBuilder:
    global _kg_builder
    _kg_builder = KnowledgeGraphBuilder(data_dir)
    return _kg_builder
