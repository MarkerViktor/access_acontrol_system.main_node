from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Union, Any, Awaitable

from aiohttp.web import Request, Response, StreamResponse, json_response
from pydantic import BaseModel

Handler = Callable[[Request, ...], Awaitable[Response]]

class ControllerRequirement(ABC):
    @abstractmethod
    async def prepare_requirement(self, request: Request) -> Response | Any: ...


class require:
    def __init__(self, *checkers: ControllerRequirement, **requirements: ControllerRequirement):
        self._checkers = checkers
        self._requirements = requirements  # Результат передаётся как keyword-аргументы в обработчик

    def __call__(self, handler: Handler) -> Handler:
        @wraps(handler)
        async def wrapper_handler(request: Request, *args, **kwargs) -> Union[Response, StreamResponse]:
            nonlocal self, handler

            for checker in self._checkers:
                checker_result = await checker.prepare_requirement(request)
                if isinstance(checker_result, Response):
                    return checker_result

            requirements_kwargs = {}
            for name, requirement in self._requirements.items():
                preparing_result = await requirement.prepare_requirement(request)
                if isinstance(preparing_result, Response):
                    return preparing_result
                requirements_kwargs[name] = preparing_result
            return await handler(request, *args, **kwargs, **requirements_kwargs)
        return wrapper_handler


def pydantic_response(model: BaseModel) -> Response:
    return json_response(text=model.json(exclude_none=False))
