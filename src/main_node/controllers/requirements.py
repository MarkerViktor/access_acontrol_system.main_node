from typing import Union, Any, Type

from aiohttp import web
from aiohttp.web_request import FileField
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ValidationError

from src.main_node.controllers.utils import ControllerRequirement
from src.main_node.services.authorization import AuthorizationService


class RoomAuth(ControllerRequirement):
    async def prepare_requirement(self, request: web.Request) -> Union[Any, web.Response]:
        auth_service: AuthorizationService = request.app['authorization']

        token_string = request.headers.get('Room-Token')
        if token_string is None:
            return web.HTTPBadRequest(text='Room-Token header is required.')

        auth = await auth_service.authorize_room(token_string)
        if not auth.token_check.known:
            return web.HTTPUnauthorized(text='Unknown Room-Token value.')

        if not auth.token_check.valid:
            return web.HTTPUnauthorized(text='Token has already invalid.')

        return auth.room_id


class AdminAuth(ControllerRequirement):
    async def prepare_requirement(self, request: web.Request) -> Union[Any, web.Response]:
        auth_service: AuthorizationService = request.app['authorization']

        token_string = request.headers.get('Admin-Token')
        if token_string is None:
            return web.HTTPBadRequest(text='Admin-Token header is required.')

        auth = await auth_service.authorize_admin(token_string)
        if not auth.token_check.known:
            return web.HTTPUnauthorized(text='Unknown token.')

        return auth.admin_id


class ImageField(ControllerRequirement):
    def __init__(self, multipart_name: str):
        self._multipart_name = multipart_name

    async def prepare_requirement(self, request: web.Request) -> Union[Any, web.Response]:
        if request.content_type != 'multipart/form-data':
            return web.HTTPBadRequest(text="Send image as multipart/form-data in field named «image».")

        post_data = await request.post()

        image_field = post_data.get(self._multipart_name)
        if image_field is None:
            return web.HTTPBadRequest(text=f"Required «{self._multipart_name}» multipart field.")

        if not isinstance(image_field, FileField):
            return web.HTTPBadRequest(text=f"Field «{self._multipart_name}» doesn't contain an image file.")

        try:
            image = Image.open(image_field.file)
        except UnidentifiedImageError:
            return web.HTTPBadRequest(text="Cannot identify image file. It's invalid.")

        return image


class PydanticPayload(ControllerRequirement):
    def __init__(self, pydantic_model: Type[BaseModel]):
        self._pydantic_model = pydantic_model

    async def prepare_requirement(self, r: web.Request) -> Union[Any, web.Response]:
        if r.content_type != 'application/json':
            return web.HTTPBadRequest(text="Required application/json content.")

        json_raw = await r.text()
        try:
            pydantic_data = self._pydantic_model.parse_raw(json_raw)
        except ValidationError as e:
            return web.HTTPBadRequest(text=f"Json data has wrong schema or types. {e}")

        return pydantic_data
