from abc import abstractmethod, ABC
from asyncio import to_thread
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

import numpy as np
from pydantic import BaseModel

from src.face_recognition import NumpyImage, Descriptor
from src.face_recognition.two_step import FaceRecognizer, FaceImageNormalizer

from src.main_node.services.utils import BaseService, Ok, Err, Result


@dataclass
class User:
    id: int
    name: str
    surname: str
    patronymic: str
    position: Optional[str] = None


@dataclass
class UserFaceDescriptor:
    id: int
    features: list[float]
    user_id: int


@dataclass
class RoomVisitReport:
    id: int
    room_id: int
    user_id: int
    datetime: datetime


@dataclass
class Room:
    id: int
    name: str


class AccessControlRepository(ABC):
    @abstractmethod
    async def create_user(self, surname: str, name: str, patronymic: str, position: str) -> User: ...

    @abstractmethod
    async def update_user(self, id_: int, surname: str, name: str, patronymic: str, position: str) -> User: ...

    @abstractmethod
    async def get_users(self) -> list[User]: ...

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    async def check_user_exist(self, user_id: int) -> bool: ...

    @abstractmethod
    async def get_user_by_descriptor_id(self, descriptor_id: int) -> Optional[User]: ...

    @abstractmethod
    async def check_access_permission_exist(self, user_id: int, room_id: int) -> bool: ...

    @abstractmethod
    async def get_all_face_descriptors(self) -> list[UserFaceDescriptor]: ...

    @abstractmethod
    async def update_descriptor_by_user_id(self, user_id: int, descriptor: list[float]) -> None: ...

    @abstractmethod
    async def get_controlling_rooms_by_manager_id(self, manager_id) -> list[Room]: ...

    @abstractmethod
    async def get_room_by_id(self, room_id: int) -> Optional[Room]: ...

    @abstractmethod
    async def get_visits_by_room_id_and_date(self, room_id: int, date_: date) -> list[RoomVisitReport]: ...

    @abstractmethod
    async def create_visit_report(self, room_id: int, user_id: int, datetime_: datetime) -> RoomVisitReport: ...

    @abstractmethod
    async def create_access_permission(self, room_id: int, user_id: int) -> None: ...

    @abstractmethod
    async def delete_access_permission_by_room_id_and_user_id(self, room_id, user_id) -> None: ...

    @abstractmethod
    async def get_accessed_users_by_room_id(self, room_id: int) -> list[User]: ...


class AccessControlService(BaseService):
    def __init__(self, repository: AccessControlRepository,
                 face_recognizer: FaceRecognizer,
                 face_image_normalizer: FaceImageNormalizer):
        self._repository = repository
        self._face_recognizer = face_recognizer
        self._face_image_normalizer = face_image_normalizer

    async def check_access_by_face(self, room_id: int, image: NumpyImage) -> 'Result[AccessCheck]':
        """Check user access to the room by his face."""
        if not self._face_recognizer.check_image_normalized(image):
            return Err(cause='Provided image is not normalized.')
        # Recognize face
        result = await to_thread(self._face_recognizer.recognize, image)
        if not result.is_known_face:
            return Ok(result=AccessCheck(is_known=False))
        # Get user by descriptor id
        user = await self._repository.get_user_by_descriptor_id(result.descriptor_id)
        if user is None:
            cause = f'Calculated descriptor is known but not bound to user. (descriptor_id = {result.descriptor_id})'
            return Err(cause=cause)
        # Check user access to the room
        have_access = await self._repository.check_access_permission_exist(user.id, room_id)
        return Ok(result=AccessCheck(is_known=True, have_access=have_access, user=user))

    async def check_access_by_descriptor(self, room_id: int, descriptor: Descriptor) -> 'Result[AccessCheck]':
        """Check user access to the room by descriptor of his face."""
        if not self._face_recognizer.check_descriptor_valid(descriptor):
            return Err(cause='Provided descriptor is invalid.')
        # Get descriptor id
        result = self._face_recognizer.recognize_by_descriptor(descriptor)
        if not result.is_known_face:
            return Ok(result=AccessCheck(is_known=False))
        # Get user by descriptor id
        user = await self._repository.get_user_by_descriptor_id(result.descriptor_id)
        if user is None:
            cause = f'Provided descriptor is known, but not bound to user. (descriptor_id = {result.descriptor_id})'
            return Err(cause=cause)
        # Check user access to the room
        have_access = await self._repository.check_access_permission_exist(user.id, room_id)
        return Ok(result=AccessCheck(is_known=True, have_access=have_access, user=user))

    async def record_visit(self, room_id: int, user_id: int, datetime_: datetime) -> 'Result[VisitRecording]':
        """Record information about room visiting if access permission exist."""
        # Check permission to the room exist
        if not await self._repository.check_access_permission_exist(user_id, room_id):
            return Ok(result=VisitRecording(allowed=False))
        # Write no visit to database_
        visit = await self._repository.create_visit_report(room_id, user_id, datetime_.astimezone())
        return Ok(result=VisitRecording(allowed=True, visit_id=visit.id))

    async def calculate_descriptor(self, image: NumpyImage) -> 'Result[AnonymousDescriptor]':
        """Calculate face descriptor based on given image."""
        if not self._face_image_normalizer.check_image_valid(image):
            return Err(cause="Provided image is invalid.")
        # Normalize image
        normalized_image = await to_thread(self._face_image_normalizer.normalize, image)
        if normalized_image is None:
            return Err(cause="Can't normalize image. Maybe there is no face.")
        # Calculate descriptor
        descriptor = await to_thread(self._face_recognizer.calculate_descriptor, normalized_image)
        anonymous_descriptor = AnonymousDescriptor(features=list(descriptor))
        return Ok(result=anonymous_descriptor)

    async def create_user(self, surname: str, name: str, patronymic: str, position: str) -> Result['UserInfo']:
        user = await self._repository.create_user(surname, name, patronymic, position)
        return Ok(result=UserInfo.from_user(user))

    async def get_all_users(self) -> Result[list['UserInfo']]:
        users = await self._repository.get_users()
        user_infos = list(map(UserInfo.from_user, users))
        return Ok(result=UserList(users=user_infos))

    async def get_user(self, user_id: int) -> Result['UserInfo']:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            return Err(cause=f'No user with provided id={user_id}')
        return Ok(result=UserInfo.from_user(user))

    async def update_user_descriptor(self, user_id: int, descriptor: Descriptor) -> Result:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            return Err(cause='Unknown user id.')
        await self._repository.update_descriptor_by_user_id(user_id, list(descriptor))
        await self._load_descriptors()
        return Result(success=True)

    async def get_controlling_rooms(self, manager_id: int) -> Result['RoomsList']:
        rooms = await self._repository.get_controlling_rooms_by_manager_id(manager_id)
        room_infos = list(map(RoomInfo.from_room, rooms))
        return Ok(result=RoomsList(rooms=room_infos))

    async def get_room(self, room_id: int) -> Result['RoomInfo']:
        room = await self._repository.get_room_by_id(room_id)
        if room is None:
            return Err(cause=f'No room with provided id={room_id}')
        return Ok(result=RoomInfo.from_room(room))

    async def get_visits(self, room_id: int, date_: date) -> Result['VisitsList']:
        visit_reports = await self._repository.get_visits_by_room_id_and_date(room_id, date_)
        visit_infos = list(map(VisitInfo.from_visit_report, visit_reports))
        return Ok(result=VisitsList(visits=visit_infos))

    async def configure_access(self, room_id: int, user_id: int, accessed: bool) -> Result:
        if accessed:
            await self._repository.create_access_permission(room_id, user_id)
        else:
            await self._repository.delete_access_permission_by_room_id_and_user_id(room_id, user_id)
        return Result(success=True)

    async def get_accessed_users(self, room_id: int) -> Result['UserList']:
        users = await self._repository.get_accessed_users_by_room_id(room_id)
        user_infos = [UserInfo.from_user(u) for u in users]
        return Ok(result=UserList(users=user_infos))

    async def _load_descriptors(self) -> None:
        """Load descriptors from DB to the ._face_recognizer()."""
        descriptors = await self._repository.get_all_face_descriptors()
        numpy_descriptors = ((d.id, np.array(d.features)) for d in descriptors)
        self._face_recognizer.update_descriptors(numpy_descriptors)

    async def init(self) -> None:
        await self._load_descriptors()


class AccessCheck(BaseModel):
    is_known: bool
    have_access: Optional[bool] = None
    user: Optional[User] = None


class VisitRecording(BaseModel):
    allowed: bool
    visit_id: Optional[int] = None


class AnonymousDescriptor(BaseModel):
    features: list[float]


class UserInfo(BaseModel):
    id: int
    surname: str
    name: str
    patronymic: str
    position: str

    @classmethod
    def from_user(cls, user: User):
        return cls(id=user.id, surname=user.surname, name=user.name,
                   patronymic=user.patronymic, position=user.position)


class UserList(BaseModel):
    users: list[UserInfo]


class RoomInfo(BaseModel):
    id: int
    name: str

    @classmethod
    def from_room(cls, room: Room):
        return cls(id=room.id, name=room.name)

class RoomsList(BaseModel):
    rooms: list[RoomInfo]


class VisitInfo(BaseModel):
    datetime: datetime
    user_id: int

    @classmethod
    def from_visit_report(cls, report: RoomVisitReport):
        return cls(datetime=report.datetime, user_id=report.user_id)

class VisitsList(BaseModel):
    visits: list[VisitInfo]
