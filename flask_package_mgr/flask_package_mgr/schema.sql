drop table if exists users;
drop table if exists packages;
drop table if exists filestore;
drop table if exists tags;

create table users (
    id          integer primary key autoincrement,
    username    varchar(255),
    password    varchar(255),
    apikey      varchar(255),
    CONSTRAINT unique_username UNIQUE(username)
    );

create table packages (
    id          integer primary key autoincrement,
    title       varchar(255),
    user_id     integer,
    FOREIGN KEY(user_id) REFERENCES users(id)
    );

create table filestore (
    id          integer primary key autoincrement,
    package     BLOB
    );

create table tags (
    id              integer primary key autoincrement,
    tag             varchar(255),
    package_id      integer,
    filestore_id    integer,
    FOREIGN KEY(package_id)     REFERENCES packages(id),
    FOREIGN KEY(filestore_id)   REFERENCES filestore(id),
    CONSTRAINT unique_tags UNIQUE (tag, package_id)
    );
