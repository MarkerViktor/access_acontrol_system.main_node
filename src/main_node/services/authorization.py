from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel

from src.main_node.services.utils import BaseService, Result, Ok, Err

from config import ROOM_TOKEN_LIFETIME_SEC


ROOM_TOKEN_LIFETIME = timedelta(seconds=ROOM_TOKEN_LIFETIME_SEC)


@dataclass
class RoomLoginToken:
    token: str
    room_id: int


@dataclass
class RoomTempToken:
    token: str
    room_id: int
    valid_before: datetime


@dataclass
class AdminToken:
    token: str
    admin_id: int


class AuthorizationRepository(ABC):
    @abstractmethod
    async def create_room_temp_token(
            self, room_id: int, valid_before: datetime) -> RoomTempToken: ...

    @abstractmethod
    async def delete_room_temp_token(self, room_id: int) -> None: ...

    @abstractmethod
    async def get_room_temp_token(self, token: str) -> Optional[RoomTempToken]: ...

    @abstractmethod
    async def get_room_login_token(self, token: str) -> Optional[RoomLoginToken]: ...

    @abstractmethod
    async def get_admin_token(self, token: str) -> Optional[AdminToken]: ...


class AuthorizationService(BaseService):
    def __init__(self, repository: AuthorizationRepository):
        self._repository = repository

    async def authorize_room(self, temp_token_string: str) -> 'RoomAuthorization':
        """
        Authorize room by temp token string.
        Token checking result:
            .token_check.known: bool – token is known,
            .token_check.valid: bool – token is valid at the checking time.
        If token is unknown or already invalid – check is not passed, so room_id is None.
        """
        # Get TempRoomToken entity
        temp_token = await self._repository.get_room_temp_token(token=temp_token_string)
        if temp_token is None:
            return RoomAuthorization(token_check=TempTokenCheck(known=False))
        # Check token is already invalid
        if temp_token.valid_before < datetime.now().astimezone():
            return RoomAuthorization(token_check=TempTokenCheck(known=True, valid=False))
        return RoomAuthorization(token_check=TempTokenCheck(known=True, valid=True), room_id=temp_token.room_id)

    async def authorize_admin(self, admin_token_string: str) -> 'AdminAuthorization':
        """
        Authorize admin by token string.
        Token checking result:
            .token_check.known: bool – token is known.
        If token is unknown – check is not passed, so room_id is None.
        """
        # Get AdminToken entity
        token = await self._repository.get_admin_token(token=admin_token_string)
        if token is None:
            return AdminAuthorization(token_check=TokenCheck(known=False))
        return AdminAuthorization(token_check=TokenCheck(known=True), admin_id=token.admin_id)

    async def log_in_room(self, login_token_string: str) -> Result['TempTokenInfo']:
        """
        Log in room by login token string.
        Token checking result:
            .token_check.known: bool – login token is known.
        If token is unknown – check is not passed, so new temp token is not creating and returning.
        """
        # Get RoomLoginToken entity
        login_token = await self._repository.get_room_login_token(token=login_token_string)
        if login_token is None:
            return Err(cause="Unknown room login token.")
        # Delete old temp token
        await self._repository.delete_room_temp_token(room_id=login_token.room_id)
        # Create new temp token
        new_token = await self._repository.create_room_temp_token(
            room_id=login_token.room_id,
            valid_before=datetime.now() + ROOM_TOKEN_LIFETIME
        )
        temp_token_info = TempTokenInfo(temp_token=new_token.token,
                                        valid_before=new_token.valid_before)
        return Ok(result=temp_token_info)


class TokenCheck(BaseModel):
    known: bool

class TempTokenCheck(TokenCheck):
    valid: Optional[bool] = None


class AdminAuthorization(BaseModel):
    token_check: TokenCheck
    admin_id: Optional[int] = None

class RoomAuthorization(BaseModel):
    token_check: TempTokenCheck
    room_id: Optional[int] = None


class TempTokenInfo(BaseModel):
    temp_token: str
    valid_before: datetime
