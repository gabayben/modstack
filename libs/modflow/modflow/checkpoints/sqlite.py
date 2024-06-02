"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/sqlite.py
"""

from contextlib import AbstractContextManager, contextmanager
import sqlite3
from types import TracebackType
from typing import Any, Iterator, Optional, Self, Type

from modflow.checkpoints import Checkpoint, CheckpointMetadata, CheckpointTuple, Checkpointer
from modstack.core.typing import Effect

class SqliteCheckpointer(Checkpointer, AbstractContextManager):
    conn: sqlite3.Connection
    is_setup: bool

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None
    ):
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

    def search(self, metadata: CheckpointMetadata, *, limit: Optional[int] = None, **kwargs) -> Effect[
        CheckpointTuple | None]:
        pass

    def get(self, **kwargs) -> Effect[CheckpointTuple | None]:
        pass

    def put(self, checkpoint: Checkpoint, metadata: CheckpointMetadata, **kwargs) -> dict[str, Any]:
        pass

    async def aput(self, checkpoint: Checkpoint, metadata: CheckpointMetadata, **kwargs) -> dict[str, Any]:
        pass