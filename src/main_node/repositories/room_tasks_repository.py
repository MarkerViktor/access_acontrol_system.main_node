from typing import Optional, Any

from src.main_node.repositories.utils import BaseRepository
from src.main_node.services import room_node_tasks_service as s


class RoomTasksRepository(BaseRepository, s.RoomTasksRepository):
    async def get_room_tasks_with_status(self, room_id: int, status: s.TaskStatus) -> list[s.RoomTask]:
        query = 'select * from "RoomTask" where "room_id" = $1 and "status" = $2'
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, room_id, status)
        return [s.RoomTask(**r) for r in records]

    async def check_manager_exist(self, id_: int):
        query = 'select from "Manager" where "id" = $1'
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, id_) is not None

    async def check_room_exist(self, id_: int):
        query = 'select from "Room" where "id" = $1'
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, id_) is not None

    async def update_task_status(self, new_status: s.TaskStatus, *task_ids: int) -> None:
        query = 'update "RoomTask" set "status" = $1 where "id" = $2'
        args = ((new_status, task_id) for task_id in task_ids)
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args)

    async def create_task(self, room_id: int, type_: s.TaskType, kwargs: dict[str, Any]) -> s.RoomTask:
        query = 'insert into "RoomTask" ("room_id", "type", "kwargs", "status")' \
                'values ($1, $2, $3, $4) returning *'
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, room_id, type_, kwargs, s.TaskStatus.UNSENT)
        return s.RoomTask(**record)

    async def get_task_by_id(self, id_: int) -> Optional[s.RoomTask]:
        query = 'select * from "RoomTask" where "id" = $1'
        async with self.pool.acquire() as conn:
            if record := await conn.fetchrow(query, id_):
                return s.RoomTask(**record)
            else:
                return None
