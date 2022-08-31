from typing import Optional
from datetime import datetime

from src.main_node.services import authorization as s
from src.main_node.repositories.utils import BaseRepository


class AuthorizationRepository(BaseRepository, s.AuthorizationRepository):
    async def create_room_temp_token(self, room_id: int, valid_before: datetime) -> s.RoomTempToken:
        query = 'insert into "RoomTempToken" ("room_id", "valid_before") values ($1, $2) returning *'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, room_id, valid_before)
        return s.RoomTempToken(**record)

    async def delete_room_temp_token(self, room_id: int) -> None:
        query = 'delete from "RoomTempToken" where "room_id" = $1'
        async with self.pool.acquire() as conn:
            await conn.execute(query, room_id)

    async def get_room_temp_token(self, token: str) -> Optional[s.RoomTempToken]:
        query = 'select * from "RoomTempToken" where "token" = $1'
        async with self.pool.acquire() as conn:
            if record := await conn.fetchrow(query, token):
                return s.RoomTempToken(**record)
            else:
                return None

    async def get_room_login_token(self, token: str) -> Optional[s.RoomLoginToken]:
        query = 'select * from "RoomLoginToken" where "token" = $1'
        async with self.pool.acquire() as conn:
            if record := await conn.fetchrow(query, token):
                return s.RoomLoginToken(**record)
            else:
                return None

    async def get_admin_token(self, token: str) -> Optional[s.AdminToken]:
        query = 'select * from "AdminToken" where "token" = $1'
        async with self.pool.acquire() as conn:
            if record := await conn.fetchrow(query, token):
                return s.AdminToken(**record)
            else:
                return None
