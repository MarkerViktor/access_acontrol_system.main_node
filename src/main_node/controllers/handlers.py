from datetime import datetime, date
from typing import Any

from aiohttp import web
from PIL.Image import Image
import numpy as np
from pydantic import BaseModel, validator

import config
from src.face_recognition import NumpyImage
from src.main_node.services.access_control import AccessControlService
from src.main_node.services.authorization import AuthorizationService
from src.main_node.services.room_node_tasks_service import RoomTasksService

from .utils import require, pydantic_response
from .requirements import RoomAuth, AdminAuth, ImageField, PydanticPayload


def convert_to_NumpyImage(image: Image) -> NumpyImage:
    return np.array(image)


@require(room_id=RoomAuth(), image=ImageField('image'))
async def check_access_by_face(r: web.Request, room_id: int, image: Image):
    access_control: AccessControlService = r.app['access_control']
    numpy_image = convert_to_NumpyImage(image)
    access_check = await access_control.check_access_by_face(room_id, numpy_image)
    return pydantic_response(access_check)


class FaceDescriptor(BaseModel):
    features: list[float]

@require(room_id=RoomAuth(), payload=PydanticPayload(FaceDescriptor))
async def check_access_by_descriptor(r: web.Request, room_id: int, payload: FaceDescriptor):
    access_control: AccessControlService = r.app['access_control']
    descriptor = np.array(payload.features)
    access_check = await access_control.check_access_by_descriptor(room_id, descriptor)
    return pydantic_response(access_check)


class VisitInfo(BaseModel):
    datetime: datetime
    user_id: int

@require(room_id=RoomAuth(), visit=PydanticPayload(VisitInfo))
async def record_visit(r: web.Request, room_id: int, visit: VisitInfo):
    access_control: AccessControlService = r.app['access_control']
    user_id, datetime_ = visit.user_id, visit.datetime
    visit_recording = await access_control.record_visit(room_id, user_id, datetime_)
    return pydantic_response(visit_recording)


@require(room_id=RoomAuth())
async def get_undone_tasks(r: web.Request, room_id: int):
    tasks_service: RoomTasksService = r.app['room_tasks']
    task_list = await tasks_service.get_unsent_tasks(room_id)
    return pydantic_response(task_list)


class TaskPerformingReport(BaseModel):
    task_id: int
    new_status: str

@require(room_id=RoomAuth(), report=PydanticPayload(TaskPerformingReport))
async def report_task_performed(r: web.Request, room_id: int, report: TaskPerformingReport):
    tasks_service: RoomTasksService = r.app['room_tasks']
    task_id, status = report.task_id, report.new_status
    result = await tasks_service.report_task_performed(room_id, task_id, status)
    return pydantic_response(result)


async def room_login(r: web.Request):
    auth_service: AuthorizationService = r.app['authorization']
    token_string = r.headers.get('Login-Token')
    if token_string is None:
        return web.HTTPBadRequest(text='Login-Token header is required.')
    room_login_ = await auth_service.log_in_room(token_string)
    return pydantic_response(room_login_)


@require(AdminAuth(), image=ImageField(multipart_name='image'))
async def calculate_descriptor(r: web.Request, image: Image):
    access_control: AccessControlService = r.app['access_control']
    numpy_image = convert_to_NumpyImage(image)
    descriptor_calculation = await access_control.calculate_descriptor(numpy_image)
    return pydantic_response(descriptor_calculation)


class NewUserFields(BaseModel):
    surname: str
    name: str
    patronymic: str
    position: str

    @validator('surname')
    @validator('name', allow_reuse=True)
    @validator('patronymic', allow_reuse=True)
    def check_name_parts(cls, value):
        if not value.isalpha() or not value[0].isupper():
            raise ValueError('Name parts have invalid format.')
        return value

    @validator('position')
    def check_position(cls, value):
        if value not in config.POSSIBLE_POSITIONS:
            raise ValueError('Unknown user position.')
        return value


@require(AdminAuth(), new_user_fields=PydanticPayload(NewUserFields))
async def create_user(r: web.Request, new_user_fields: NewUserFields):
    access_control: AccessControlService = r.app['access_control']
    user = await access_control.create_user(
        surname=new_user_fields.surname,
        name=new_user_fields.name,
        patronymic=new_user_fields.patronymic,
        position=new_user_fields.position,
    )
    return pydantic_response(user)


@require(AdminAuth())
async def get_users(r: web.Request):
    access_control: AccessControlService = r.app['access_control']
    # TODO: Добавить фильтры
    users = await access_control.get_all_users()
    return pydantic_response(users)


class UserId(BaseModel):
    user_id: int

@require(AdminAuth(), payload=PydanticPayload(UserId))
async def get_user(r: web.Request, payload: UserId):
    access_control: AccessControlService = r.app['access_control']
    user = await access_control.get_user(payload.user_id)
    return pydantic_response(user)

class DescriptorUpdating(BaseModel):
    user_id: int
    descriptor: FaceDescriptor

@require(AdminAuth(), descriptor_updating=PydanticPayload(DescriptorUpdating))
async def update_user_descriptor(r: web.Request, descriptor_updating: DescriptorUpdating):
    access_control: AccessControlService = r.app['access_control']
    descriptor = np.array(descriptor_updating.descriptor.features)
    result = await access_control.update_user_descriptor(descriptor_updating.user_id, descriptor)
    return pydantic_response(result)


class ManagerId(BaseModel):
    manager_id: int

@require(AdminAuth(), payload=PydanticPayload(ManagerId))
async def get_controlling_rooms(r: web.Request, payload: ManagerId):
    access_control: AccessControlService = r.app['access_control']
    rooms = await access_control.get_controlling_rooms(payload.manager_id)
    return pydantic_response(rooms)


class RoomId(BaseModel):
    room_id: int

@require(AdminAuth(), payload=PydanticPayload(RoomId))
async def get_room(r: web.Request, payload: RoomId):
    access_control: AccessControlService = r.app['access_control']
    room = await access_control.get_room(payload.room_id)
    return pydantic_response(room)


class VisitParams(BaseModel):
    room_id: int
    date: date

@require(AdminAuth(), params=PydanticPayload(VisitParams))
async def get_visits(r: web.Request, params: VisitParams):
    access_control: AccessControlService = r.app['access_control']
    visits = await access_control.get_visits(params.room_id, params.date)
    return pydantic_response(visits)


class AccessConfiguration(BaseModel):
    room_id: int
    user_id: int
    accessed: bool

@require(AdminAuth(), access_config=PydanticPayload(AccessConfiguration))
async def configure_room_access(r: web.Request, access_config: AccessConfiguration):
    access_control: AccessControlService = r.app['access_control']
    result = await access_control.configure_access(
        access_config.room_id, access_config.user_id, access_config.accessed)
    return pydantic_response(result)


class TaskCreation(BaseModel):
    room_id: int
    type: str
    kwargs: dict[str, Any]


@require(AdminAuth(), payload=PydanticPayload(TaskCreation))
async def create_task(r: web.Request, payload: TaskCreation):
    tasks_service: RoomTasksService = r.app['room_tasks']
    task = await tasks_service.create_task(payload.room_id, payload.type, payload.kwargs)
    return pydantic_response(task)


@require(AdminAuth(), payload=PydanticPayload(RoomId))
async def get_accessed_users(r: web.Request, payload: RoomId):
    access_control: AccessControlService = r.app['access_control']
    accessed_users = await access_control.get_accessed_users(payload.room_id)
    return pydantic_response(accessed_users)
