from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from src.main_node.services.utils import BaseService, Ok, Err, Result


class TaskStatus(str, Enum):
    UNSENT = 'UNSENT'
    SENT = 'SENT'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'
    PERFORMING_ERROR = 'PERFORMING_ERROR'
    KWARGS_ERROR = 'PARAMETERS_ERROR'
    NO_SUITABLE_HANDLER_ERROR = 'NO_SUITABLE_HANDLER_ERROR'


class TaskType(str, Enum):
    """Тип задачи для узла помещения."""
    OPEN_DOOR = 'OPEN_DOOR'
    SCHEDULE_TASK = 'SCHEDULE_TASK'
    CANCEL_TASK = 'CANCEL_TASK'


@dataclass
class RoomTask:
    """Задача для узла помещения."""
    id: int
    room_id: int
    type: TaskType
    kwargs: dict[str, Any]
    status: TaskStatus

    def __repr__(self):
        return f'Task(id={self.id},type={self.type})'


class RoomTasksRepository(ABC):
    @abstractmethod
    async def get_room_tasks_with_status(self, room_id: int, status: TaskStatus) -> list[RoomTask]: ...

    @abstractmethod
    async def check_manager_exist(self, id_: int): ...

    @abstractmethod
    async def check_room_exist(self, id_: int): ...

    @abstractmethod
    async def update_task_status(self, new_status: TaskStatus, *task_ids: int) -> None: ...

    @abstractmethod
    async def create_task(self, room_id: int, type_: TaskType, kwargs: dict[str, Any]) -> RoomTask: ...

    @abstractmethod
    async def get_task_by_id(self, id_: int) -> Optional[RoomTask]: ...


class RoomTasksService(BaseService):
    def __init__(self, repository: RoomTasksRepository):
        self._repository = repository

    async def get_unsent_tasks(self, room_id: int) -> Result['TaskList']:
        """Load tasks having status «undone» set to the room with provided id."""
        tasks = await self._repository.get_room_tasks_with_status(room_id, TaskStatus.UNSENT)
        await self._repository.update_task_status(TaskStatus.SENT, *(t.id for t in tasks))
        task_views = [TaskView.parse_obj(vars(t)) for t in tasks]
        return Ok(result=TaskList(tasks=task_views))

    async def report_task_performed(self, room_id: int, task_id: int, new_status: str) -> Result:
        """"""
        # Get task by id
        task = await self._repository.get_task_by_id(task_id)
        if task is None:
            return Err(cause='No task with provided id.')
        # Check the task bounded to the room
        if task.room_id != room_id:
            return Err(cause="Room hasn't task with provided id.")
        # Check new status valid
        if new_status not in TaskStatus.__members__.values():
            cause = f'Unknown status. Possible statuses: {", ".join(map(lambda s: s.value, TaskStatus))}.'
            return Err(cause=cause)
        await self._repository.update_task_status(TaskStatus(new_status), task_id)
        return Result(success=True)

    async def create_task(self, room_id: int, type_: str, kwargs: dict[str, Any]) -> Result[RoomTask]:
        # Check room exist
        if not await self._repository.check_room_exist(room_id):
            return Err(cause='Unknown room.')
        if type_ not in TaskType.__members__.values():
            return Err(cause='Unknown task type.')
        task = await self._repository.create_task(room_id, TaskType(type_), kwargs)
        return Ok(result=TaskView.parse_obj(vars(task)))


class TaskView(BaseModel):
    id: int
    type: TaskType
    kwargs: dict[str, Any]


class TaskList(BaseModel):
    tasks: list[TaskView]
