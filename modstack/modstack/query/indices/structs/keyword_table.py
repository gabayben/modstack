from pydantic import Field

from modstack.artifacts import Artifact
from modstack.query.indices import IndexStruct

class KeywordTable(IndexStruct):
    """A table mapping keywords to artifact ids."""

    table: dict[str, set[str]] = Field(default_factory=dict)

    @property
    def keywords(self) -> set[str]:
        """Get all keywords in the table."""
        return set(self.table.keys())

    @property
    def artifact_ids(self) -> set[str]:
        """Get all artifact ids."""
        return set.union(*self.table.values())

    @property
    def size(self) -> int:
        """Get the size of the table."""
        return len(self.table)

    def add_artifact(self, keywords: list[str], artifact: Artifact) -> None:
        """Add artifact to table."""
        for keyword in set(keywords):
            if keyword not in self.table:
                self.table[keyword] = set()
            self.table[keyword].add(artifact.id)