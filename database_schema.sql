create table "Admin"
(
    id       serial,
    nickname     text not null,
    primary key (id)
);

-- Пользователь системы контроля доступа
create table "User"
(
    id         serial,
    name       text not null,
    surname    text not null,
    extra_info text,
    primary key (id)
);

-- Помещение
create table "Room"
(
    id   serial,
    name text not null,
    primary key (id)
);

-- Доступ пользователя в помещение
create table "UserRoomAccessPermission"
(
    id      serial,
    user_id integer not null,
    room_id integer not null,
    primary key (id),
    unique (user_id, room_id),
    constraint user_id
        foreign key (user_id) references "User"
            on update cascade on delete cascade,
    constraint room_id
        foreign key (room_id) references "Room"
            on update cascade on delete cascade
);

-- Отчёт о предоставлении доступа в помещение
create table "RoomVisitReport"
(
    id       serial,
    room_id  integer                  not null,
    user_id  integer                  not null,
    datetime timestamp with time zone not null,
    primary key (id),
    constraint user_id
        foreign key (user_id) references "User"
            on update cascade on delete cascade,
    constraint room_id
        foreign key (room_id) references "Room"
            on update cascade on delete cascade

);

-- Дескриптор лица пользователя
create table "UserFaceDescriptor"
(
    id       serial,
    features double precision[128] not null,
    user_id  integer               not null,
    primary key (id),
    constraint user_id
        foreign key (user_id) references "User"
            on update cascade on delete cascade
);

-- Управляющий помещения
create table "Manager"
(
    id integer not null,
    primary key (id)
);

-- Разрешение на управление помещением
create table "ManagerRoomControlPermission"
(
    id         serial,
    room_id    integer not null,
    manager_id integer not null,
    primary key (id),
    unique (room_id, manager_id),
    constraint room_id
        foreign key (room_id) references "Room"
            on update cascade on delete cascade,
    constraint manager_id
        foreign key (manager_id) references "Manager"
            on update cascade on delete cascade
);

-- Задание узлу помещения
create table "RoomTask"
(
    id         serial,
    room_id    integer     not null,
    type       varchar(50) not null,
    kwargs     json        not null,
    status     varchar(50) not null,
    primary key (id),
    constraint room_id
        foreign key (room_id) references "Room"
            on update cascade on delete cascade
);

-- Генератор токенов
create function generate_token() returns character varying
    language sql
as
$$
select (md5(random()::text))::varchar(32)
$$;


-- Токен администратора
create table "AdminToken"
(
    token    varchar(32) not null default generate_token(),
    admin_id integer     not null unique,
    primary key (token),
    constraint admin_id
        foreign key (admin_id) references "Admin"
            on update cascade on delete cascade
);

-- Токен авторизации помещения
create table "RoomLoginToken"
(
    token   varchar(32) not null default generate_token(),
    room_id integer     not null unique,
    primary key (token),
    constraint room_id
        foreign key (room_id) references "Room"
            on update cascade on delete cascade
);

-- Временный токен помещения
create table "RoomTempToken"
(
    token        varchar(32)                not null default generate_token(),
    room_id      integer                    not null unique,
    valid_before timestamp with time zone   not null,
    primary key (token),
    constraint room_id
        foreign key (room_id) references "Room"
            on update cascade on delete cascade
);
