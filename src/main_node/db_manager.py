import json
from typing import TypedDict

import asyncpg


class DatabaseConfig(TypedDict):
    host: str
    port: int
    database: str
    user: str
    password: str


class DatabaseManager:
    def __init__(self, config: DatabaseConfig):
        self._config = config
        self._connection_pool: asyncpg.Pool | None = None

    async def connect(self):
        self._connection_pool = await asyncpg.create_pool(**self._config, init=init_connection)

    async def close(self):
        if self._connection_pool is not None:
            await self._connection_pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        assert self._connection_pool is not None
        return self._connection_pool


async def init_connection(conn: asyncpg.Connection):
    await conn.set_type_codec(
        'json',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog',
    )