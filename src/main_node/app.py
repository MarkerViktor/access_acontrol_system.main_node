from aiohttp import web

from src.face_recognition.two_step import FaceRecognizer, FaceImageNormalizer
from src.face_recognition.backends.dlib_ import DlibRecognizer, DlibDetector, DlibNormalizer

from src.main_node.db_manager import DatabaseManager

from src.main_node.services.access_control import AccessControlService
from src.main_node.services.authorization import AuthorizationService
from src.main_node.services.room_node_tasks_service import RoomTasksService

from src.main_node.repositories.access_control_repository import AccessControlRepository
from src.main_node.repositories.authorization_repository import AuthorizationRepository
from src.main_node.repositories.room_tasks_repository import RoomTasksRepository

from src.main_node.controllers import handlers

import config

routes = [
        web.post(  # Проверить доступ по нормализованному изображению лица
            '/access/check_by_face', handlers.check_access_by_face),
        web.post(  # Проверить доступ по дескриптору лица
            '/access/check_by_descriptor', handlers.check_access_by_descriptor),
        web.post(  # Отчёт о посещении помещения
            '/access/report_visit', handlers.record_visit),
        web.post(  # Рассчитать дескриптор лица для самого крупного изображения с лицом
            '/access/calculate_descriptor', handlers.calculate_descriptor),
        web.post(  # Обновить дескриптор лица пользователя
            '/access/update_descriptor', handlers.update_user_descriptor),
        web.get(  # Получить список пользователей, имеющих доступ в помещение
            '/access/users', handlers.get_accessed_users),
        web.get(  # Получить невыполненные задачи узла помещения
            '/tasks/undone', handlers.get_undone_tasks),
        web.post(  # Отчёт о выполнении задачи
            '/task/report', handlers.report_task_performed),
        web.post(  # Авторизация узла помещения
            '/authorization/room_login', handlers.room_login),
        web.post(  # Создать нового пользователя
            '/user', handlers.create_user),
        web.get(  # Получить список всех пользователей
            '/users', handlers.get_users),
        web.get(  # Получить информацию о пользователе по идентификатору
            '/user', handlers.get_user),
        web.get(  # Получить список помещений, управляемых администраторам
            '/rooms', handlers.get_controlling_rooms),
        web.get(  # Получить информацию о помещении
            '/room', handlers.get_room),
        web.get(  # Получить список посещений помещения в заданную дату
            '/access/visits', handlers.get_visits),
        web.post(  # Конфигурация доступа пользователя в помещение
            '/access/configure', handlers.configure_room_access),
        web.post(  # Создать новую задачу узлу помещения
            '/task', handlers.create_task),
    ]

def init() -> web.Application:
    app = web.Application()

    db_manager = DatabaseManager(config.database_config)
    setup_signals(app, db_manager.connect, db_manager.close)

    access_control = AccessControlService(
        repository=AccessControlRepository(db_manager),
        face_recognizer=FaceRecognizer(
            recognizer=DlibRecognizer(),
        ),
        face_image_normalizer=FaceImageNormalizer(
            detector=DlibDetector(),
            normalizer=DlibNormalizer(),
        ),
    )
    setup_signals(app, access_control.init, access_control.deinit)
    app['access_control'] = access_control

    room_tasks = RoomTasksService(
        repository=RoomTasksRepository(db_manager)
    )
    setup_signals(app, room_tasks.init, room_tasks.deinit)
    app['room_tasks'] = room_tasks

    authorization = AuthorizationService(
        repository=AuthorizationRepository(db_manager)
    )
    setup_signals(app, authorization.init, authorization.deinit)
    app['authorization'] = authorization

    app.add_routes(routes)
    return app


def setup_signals(app: web.Application, on_startup, on_shutdown):
    def wrap(func):
        # Aiohttp signals must have single positional argument, which is useless is the case.
        async def wrapper(_):
            await func()
        return wrapper
    app.on_startup.append(wrap(on_startup))
    app.on_shutdown.append(wrap(on_shutdown))
