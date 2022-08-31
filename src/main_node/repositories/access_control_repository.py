from datetime import datetime, date
from typing import Optional

from src.main_node.repositories.utils import BaseRepository
from src.main_node.services import access_control as s


class AccessControlRepository(BaseRepository, s.AccessControlRepository):
    async def get_user_by_descriptor_id(self, descriptor_id: int) -> Optional[s.User]:
        query = 'select * from "User" where "id" = ' \
                '(select "user_id" from "UserFaceDescriptor" where "id" = $1)'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, descriptor_id)
        return s.User(**record) if record else None

    async def get_user_by_id(self, user_id: int) -> Optional[s.User]:
        query = 'select * from "User" where "id" = $1'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, user_id)
        return s.User(**record) if record else None

    async def check_access_permission_exist(self, user_id: int, room_id: int) -> bool:
        query = 'select from "UserRoomAccessPermission" where "room_id" = $1 and "user_id" = $2'
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, room_id, user_id) is not None

    async def check_user_exist(self, user_id: int) -> bool:
        query = 'select from "User" where "id" = $1'
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, user_id) is not None

    async def create_visit_report(self, room_id: int, user_id: int, datetime_: datetime) -> s.RoomVisitReport:
        query = 'insert into "RoomVisitReport" ("room_id", "user_id", "datetime") ' \
                'values ($1, $2, $3) returning *'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, room_id, user_id, datetime_)
        return s.RoomVisitReport(**record)

    async def get_all_face_descriptors(self) -> list[s.UserFaceDescriptor]:
        query = 'select * from "UserFaceDescriptor"'
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query)
        descriptors = [s.UserFaceDescriptor(**r) for r in records]
        return descriptors

    async def create_user(self, surname: str, name: str, patronymic: str, position: str) -> s.User:
        query = 'insert into "User" ("surname", "name", "patronymic", "position") ' \
                'values ($1, $2, $3, $4) returning *'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, surname, name, patronymic, position)
        return s.User(**record)

    async def update_user(self, id_: int, surname: str, name: str, patronymic: str, position: str) -> s.User:
        query = 'update "User" set ("surname", "name", "patronymic", "position") = ($2, $3, $4, $5)' \
                'where "id" = $1 returning *'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, id_, surname, name, patronymic, position)
        return s.User(**record)

    async def get_users(self) -> list[s.User]:
        query = 'select * from "User"'
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query)
        return [s.User(**r) for r in records]

    async def update_descriptor_by_user_id(self, user_id: int, descriptor: list[float]) -> None:
        query_delete = 'delete from "UserFaceDescriptor" where "user_id" = $1'
        query_insert = 'insert into "UserFaceDescriptor" ("user_id", "features") values ($1, $2)'
        async with self.pool.acquire() as conn:
            await conn.execute(query_delete, user_id)
            await conn.execute(query_insert, user_id, descriptor)

    async def get_controlling_rooms_by_manager_id(self, manager_id: int) -> list[s.Room]:
        query = 'select "Room".* from "Room"' \
                'join "ManagerRoomControlPermission" MRCP ' \
                'on "Room".id = MRCP.room_id ' \
                'where MRCP.manager_id = $1'
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, manager_id)
        return [s.Room(**r) for r in records]

    async def get_room_by_id(self, room_id: int) -> Optional[s.Room]:
        query = 'select * from "Room" where id = $1'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, room_id)
        return s.Room(**record)

    async def get_visits_by_room_id_and_date(self, room_id: int, date_: date) -> list[s.RoomVisitReport]:
        query = 'select * from "RoomVisitReport" where (room_id, date(datetime)) = ($1, $2)'
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, room_id, date_)
        return [s.RoomVisitReport(**r) for r in records]

    async def create_access_permission(self, room_id, user_id) -> None:
        query = 'insert into "UserRoomAccessPermission" (room_id, user_id) ' \
                'values ($1, $2) on conflict do nothing'
        async with self.pool.acquire() as conn:
            await conn.execute(query, room_id, user_id)

    async def delete_access_permission_by_room_id_and_user_id(self, room_id, user_id) -> None:
        query = 'delete from "UserRoomAccessPermission" where (room_id, user_id) = ($1, $2)'
        async with self.pool.acquire() as conn:
            await conn.execute(query, room_id, user_id)

    async def get_accessed_users_by_room_id(self, room_id: int) -> list[s.User]:
        query = 'select "User".* from "User"' \
                'join "UserRoomAccessPermission" URAP ' \
                'on "User".id = URAP.user_id ' \
                'where URAP.room_id = $1'
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, room_id)
        return [s.User(**r) for r in records]
