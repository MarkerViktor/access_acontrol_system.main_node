from typing import TypeVar, Generic, Protocol

from pydantic import BaseModel


class BaseService(Protocol):
    async def init(self) -> None: ...

    async def deinit(self) -> None: ...


RE = TypeVar('RE', bound=BaseModel)

class Result(BaseModel, Generic[RE]):
    success: bool

class Ok(Result[RE]):
    result: RE
    success = True

class Err(Result):
    cause: str
    success = False
