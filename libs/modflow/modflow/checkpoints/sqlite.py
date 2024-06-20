"""
Credit to LangGraph -
https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/sqlite.py
https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/aiosqlite.py
"""

import asyncio
from contextlib import AbstractAsyncContextManager, AbstractContextManager, contextmanager
from hashlib import md5
import json
import sqlite3
import threading
from types import TracebackType
from typing import Any, AsyncIterator, Iterator, Optional, Self, Sequence, Type

import aiosqlite

from modflow.channels import Channel, EmptyChannelError
from modflow.checkpoints import Checkpoint, CheckpointMetadata, SavedCheckpoint, Checkpointer
from modflow.serde import SerializerProtocol

SETUP_SCRIPT = """
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

class SqliteCheckpointer(Checkpointer, AbstractContextManager, AbstractAsyncContextManager):
    conn: sqlite3.Connection
    async_conn: aiosqlite.Connection
    lock: threading.Lock
    async_lock: asyncio.Lock
    is_setup: bool

    def __init__(
        self,
        conn: sqlite3.Connection,
        async_conn: aiosqlite.Connection,
        *,
        serde: Optional[SerializerProtocol] = None
    ):
        super().__init__(serde=serde)
        self.conn = conn
        self.async_conn = async_conn
        self.lock = threading.Lock()
        self.async_lock = asyncio.Lock()
        self.is_setup = False

    @classmethod
    def from_conn_string(cls, conn_string: str) -> Self:
        return cls(
            sqlite3.Connection(conn_string, check_same_thread=False),
            aiosqlite.connect(conn_string)
        )

    def __enter__(self) -> Self:
        return self

    async def __aenter__(self) -> Self:
        return self

    def __exit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None
    ) -> Optional[bool]:
        return self.conn.close()

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> Optional[bool]:
        if self.is_setup:
            return await self.async_conn.close()

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
        self.conn.executescript(SETUP_SCRIPT)
        self.is_setup = True

    async def asetup(self) -> None:
        async with self.async_lock:
            if self.is_setup:
                return
            if not self.async_conn.is_alive():
                await self.async_conn
            async with self.async_conn.executescript(SETUP_SCRIPT):
                await self.async_conn.commit()
            self.is_setup = True

    def get_many(
        self,
        filters: Optional[dict[str, Any]] = None,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> Iterator[SavedCheckpoint]:
        where, param_values = _search_where(filters, **kwargs)
        query = f"""
            SELECT thread_id, thread_ts, checkpoint, metadata
            FROM checkpoints
            {where}
            ORDER BY thread_ts DESC
        """
        if limit:
            query += f' LIMIT {limit}'
        with self.cursor(transaction=False) as cursor:
            cursor.execute(query, param_values)
            for thread_id, thread_ts, checkpoint, metadata in cursor:
                yield SavedCheckpoint(
                    self.serde.loads(checkpoint),
                    self.serde.loads(metadata) if metadata is not None else {},
                    {
                        'thread_id': thread_id,
                        'thread_ts': thread_ts
                    }
                )

    async def aget_many(
        self,
        filters: Optional[dict[str, Any]] = None,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[SavedCheckpoint]:
        await self.asetup()
        where, param_values = _search_where(filters, **kwargs)
        query = f"""
            SELECT thread_id, thread_ts, checkpoint, metadata
            FROM checkpoints
            {where}
            ORDER BY thread_ts DESC
        """
        if limit:
            query += f' LIMIT {limit}'
        async with self.async_conn.execute(query, param_values) as cursor:
            async for thread_id, thread_ts, checkpoint, metadata in cursor:
                yield SavedCheckpoint(
                    self.serde.loads(checkpoint),
                    self.serde.loads(metadata) if metadata is not None else {},
                    {
                        'thread_id': thread_id,
                        'thread_ts': thread_ts
                    }
                )

    def get(self, **kwargs) -> Optional[SavedCheckpoint]:
        with self.cursor(transaction=False) as cursor:
            if kwargs.get('thread_ts'):
                cursor.execute(
                    f"""
                        SELECT parent_ts, checkpoint, metadata 
                        FROM checkpoints
                        WHERE thread_id = ? and thread_ts = ?
                    """,
                    (str(kwargs['thread_id']), kwargs['thread_ts'])
                )
                if value := cursor.fetchone():
                    return SavedCheckpoint(
                        self.serde.loads(value[1]),
                        self.serde.loads(value[2]) if value[2] is not None else {},
                        {
                            'thread_id': kwargs['thread_id'],
                            'thread_ts': value[0]
                        } if value[0] else None
                    )
            else:
                cursor.execute(
                    f"""
                        SELECT thread_id, thread_ts, parent_ts, checkpoint, metadata
                        FROM checkpoints
                        WHERE thread_id = ?
                        ORDER BY DESC
                        LIMIT 1
                    """,
                    (str(kwargs['thread_id']),)
                )
                if value := cursor.fetchone():
                    return SavedCheckpoint(
                        self.serde.loads(value[4]),
                        self.serde.loads(value[5]) if value[5] is not None else {},
                        {
                            'thread_id': value[0],
                            'thread_ts': value[1],
                            'parent_ts': value[2]
                        } if value[2] else None
                    )

    async def aget(self, **kwargs) -> Optional[SavedCheckpoint]:
        await self.asetup()
        if kwargs.get('thread_ts', None):
            async with self.async_conn.execute(
                f"""
                    SELECT parent_ts, checkpoint, metadata 
                    FROM checkpoints
                    WHERE thread_id = ? and thread_ts = ?
                """,
                (str(kwargs['thread_id']), kwargs['thread_ts'])
            ) as cursor:
                if value := await cursor.fetchone():
                    return SavedCheckpoint(
                        self.serde.loads(value[1]),
                        self.serde.loads(value[2]) if value[2] is not None else {},
                        {
                            'thread_id': kwargs['thread_id'],
                            'thread_ts': value[0]
                        } if value[0] else None
                    )
        else:
            async with self.async_conn.execute(
                f"""
                    SELECT thread_id, thread_ts, parent_ts, checkpoint, metadata
                    FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY DESC
                    LIMIT 1
                """,
                (str(kwargs['thread_id']),)
            ) as cursor:
                if value := await cursor.fetchone():
                    return SavedCheckpoint(
                        self.serde.loads(value[3]),
                        self.serde.loads(value[4]) if value[4] is not None else {},
                        {
                            'thread_id': value[0],
                            'thread_ts': value[1],
                            'parent_ts': value[2]
                        } if value[2] else None
                    )

    def put(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        with self.lock, self.cursor() as cursor:
            cursor.execute(
                f"""
                    INSERT OR REPLACE INTO checkpoints 
                    (thread_id, thread_ts, parent_ts, checkpoint, metadata) (?, ?, ?, ?, ?)
                """,
                (
                    str(kwargs['thread_id']),
                    checkpoint['id'],
                    kwargs.get('thread_ts', None),
                    self.serde.dumps(kwargs['checkpoint']),
                    self.serde.dumps(kwargs.get('metadata', {}))
                )
            )
        return {
            'thread_id': kwargs['thread_id'],
            'thread_ts': checkpoint['id']
        }

    async def aput(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        await self.asetup()
        async with self.async_conn.execute(
            f"""
                INSERT OR REPLACE INTO checkpoints 
                (thread_id, thread_ts, parent_ts, checkpoint, metadata) (?, ?, ?, ?, ?)
            """,
            (
                str(kwargs['thread_id']),
                checkpoint['id'],
                kwargs.get('thread_ts', None),
                self.serde.dumps(kwargs['checkpoint']),
                self.serde.dumps(kwargs.get('metadata', {}))
            )
        ):
            await self.async_conn.commit()
        return {
            'thread_id': kwargs['thread_id'],
            'thread_ts': checkpoint['id']
        }

    def get_next_version(
        self,
        current: Optional[str],
        channel: Channel
    ) -> str:
        if current is None:
            current_version = 0
        else:
            current_version = current.split('.')[0]
        next_version = current_version + 1
        try:
            next_hash = md5(self.serde.dumps(channel.checkpoint())).hexdigest()
        except EmptyChannelError:
            next_hash = ''
        return f'{next_version:032}.{next_hash}'

def _metadata_predicate(filters: dict[str, Any]) -> tuple[Sequence[str], Sequence[Any]]:
    """
    Return WHERE clause predicates for (a)search() given metadata filter.

    This method returns a tuple of a string and a tuple of values. The string
    is the parametered WHERE clause predicate (excluding the WHERE keyword):
    "column1 = ? AND column2 IS ?". The tuple of values contains the values
    for each of the corresponding parameters.
    """
    def where_value(query_value: Optional[Any]) -> tuple[str, Optional[Any]]:
        if query_value is None:
            return 'IS ?', None
        elif isinstance(query_value, (int, float, str)):
            return '= ?', query_value
        elif isinstance(query_value, bool):
            return '= ?', 1 if query_value else 0
        elif isinstance(query_value, (list, dict)):
            return '= ?', json.dumps(query_value, separators=(',', ':'))
        return '= ?', str(query_value)

    predicates = []
    param_values = []

    # process metadata query
    for query_key, query_value in filters.items():
        operator, param_value = where_value(query_value)
        predicates.append(
            f"json_extract(CAST(metadata as TEXT), '$.{query_key}') {query_value}"
        )
        param_values.append(param_value)

    return predicates, param_values

def _search_where(filters: Optional[dict[str, Any]], **kwargs) -> tuple[str, Sequence[Any]]:
    """
    Return WHERE clause predicates for (a)search() given metadata filters.

    This method returns a tuple of a string and a tuple of values. The string
    is the parameterized WHERE clause predicate (including the WHERE keyword):
    "WHERE column1 = ? AND column2 IS ?". The tuple of values contains the
    values for each of the corresponding parameters.
    """
    wheres = []
    param_values = []

    # construct predicate for config
    wheres.append('thread_id = ?')
    param_values.append(kwargs['thread_id'])
    wheres.append('thread_ts < ?')
    param_values.append(kwargs['thread_ts'])

    # construct predicate for metadata filters
    if filters:
        metadata_predicates, metadata_values = _metadata_predicate(filters)
        wheres.extend(metadata_predicates)
        param_values.extend(metadata_values)

    return f'WHERE {' AND '.join(wheres)}' if wheres else '', param_values