import asyncpg

from src.main_node.db_manager import DatabaseManager


class BaseRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.__manager = db_manager

    @property
    def pool(self) -> asyncpg.Pool:
        return self.__manager.pool
