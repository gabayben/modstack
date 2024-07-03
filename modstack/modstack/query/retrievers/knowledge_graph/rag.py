from modstack.artifacts import Artifact
from modstack.query.retrievers import KnowledgeGraphQuery
from modstack.query.retrievers.knowledge_graph.base import KnowledgeGraphBaseRetriever

class KnowledgeGraphRAGRetriever(KnowledgeGraphBaseRetriever):
    def _invoke(self, query: KnowledgeGraphQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: KnowledgeGraphQuery, **kwargs) -> list[Artifact]:
        pass