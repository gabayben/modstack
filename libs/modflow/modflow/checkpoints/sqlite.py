"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/sqlite.py
"""

from contextlib import AbstractContextManager, contextmanager
import sqlite3
import threading
from types import TracebackType
from typing import Any, AsyncIterator, Iterator, Optional, Self, Type

from modflow.checkpoints import Checkpoint, CheckpointMetadata, CheckpointTuple, Checkpointer
from modflow.serde import SerializerProtocol

class SqliteCheckpointer(Checkpointer, AbstractContextManager):
    conn: sqlite3.Connection
    is_setup: bool

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        serde: Optional[SerializerProtocol] = None
    ):
        super().__init__(serde=serde)
        self.conn = conn
        self.is_setup = False
        self.lock = threading.Lock()

    @classmethod
    def from_conn_string(cls, conn_string: str) -> Self:
        return cls(sqlite3.Connection(conn_string, check_same_thread=False))

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None
    ) -> None:
        self.conn.close()

    @contextmanager
    def cursor(self, transaction: bool = True) -> Iterator[sqlite3.Cursor]:
        """
        Get a cursor for the SQLite database.

        This method returns a cursor for the SQLite database. It is used internally
        by the SqliteCheckpointer and should not be called directly by the user.

        Args:
            transaction (bool): Whether to commit the transaction when the cursor is closed. Defaults to True.

        Yields:
            sqlite3.Cursor: A cursor for the SQLite database.
        """
        self.setup()
        cursor = self.conn.cursor()
        try:
            yield cursor
        finally:
            if transaction:
                self.conn.commit()
            cursor.close()

    def setup(self) -> None:
        """
        Set up the checkpoint database.

        This method creates the necessary tables in the SQLite database if they don't
        already exist. It is called automatically when needed and should not be called
        directly by the user.
        """
        if self.is_setup:
            return
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT NOT NULL,
                thread_ts TEXT NOT NULL,
                parent_ts TEXT,
                checkpoint BLOB,
                metadata BLOB,
                PRIMARY KEY (thread_id, thread_ts)
            );
            """
        )
        self.is_setup = True

    def search(
        self,
        metadata: CheckpointMetadata,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> Iterator[CheckpointTuple]:
        pass

    async def asearch(
        self,
        metadata: CheckpointMetadata,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[CheckpointTuple]:
        pass

    def get_list(self, limit: Optional[int] = None, **kwargs) -> Iterator[CheckpointTuple]:
        pass

    async def aget_list(self, limit: Optional[int] = None, **kwargs) -> AsyncIterator[CheckpointTuple]:
        pass

    def get(self, **kwargs) -> Optional[CheckpointTuple]:
        pass

    async def aget(self, **kwargs) -> Optional[CheckpointTuple]:
        pass

    def put(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

    async def aput(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

def _metadata_predicate(metadata: CheckpointMetadata) -> tuple[str, tuple[Any, ...]]:
    """
    Return WHERE clause predicates for (a)search() given metadata filter.

    This method returns a tuple of a string and a tuple of values. The string
    is the parametered WHERE clause predicate (excluding the WHERE keyword):
    "column1 = ? AND column2 IS ?". The tuple of values contains the values
    for each of the corresponding parameters.
    """