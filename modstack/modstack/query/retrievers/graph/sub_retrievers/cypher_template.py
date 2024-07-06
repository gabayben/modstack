from modstack.artifacts import Artifact
from modstack.query.retrievers import GraphIndexQuery, GraphSubRetriever

class CypherTemplateRetriever(GraphSubRetriever):
    def _retrieve(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass

    async def _aretrieve(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass