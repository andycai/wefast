--
-- File generated with SQLiteStudio v3.4.4 on Sun Nov 24 15:31:37 2024
--
-- Text encoding used: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: logs
DROP TABLE IF EXISTS logs;

CREATE TABLE IF NOT EXISTS logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id      TEXT,
    package     TEXT,
    role_name   TEXT,
    device      TEXT,
    log_message TEXT,
    log_time    INTEGER,
    log_type    TEXT,
    log_stack   TEXT,
    create_at   INTEGER
);

INSERT INTO logs (
                     id,
                     app_id,
                     package,
                     role_name,
                     device,
                     log_message,
                     log_time,
                     log_type,
                     log_stack,
                     create_at
                 )
                 VALUES (
                     1,
                     'xj202409',
                     'dq1.xjgame.com',
                     '逆风',
                     'MI 15 Utral',
                     'Error',
                     1725850357000,
                     'Error',
                     '1. asdfklkjaljljl 2. iojfjlakdfjklajl',
                     1725850357000
                 );


-- Table: stats_infos
DROP TABLE IF EXISTS stats_infos;

CREATE TABLE IF NOT EXISTS stats_infos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login_id      INTEGER,
    fps           INTEGER,
    total_mem     INTEGER,
    used_mem      INTEGER,
    mono_used_mem INTEGER,
    mono_heap_mem INTEGER,
    texture       INTEGER,
    mesh          INTEGER,
    animation     INTEGER,
    audio         INTEGER,
    font          INTEGER,
    text_asset    INTEGER,
    shader        INTEGER,
    pic           TEXT,
    process       TEXT,
    stats_time    INTEGER,
    created_at    INTEGER
);


-- Table: stats_records
DROP TABLE IF EXISTS stats_records;

CREATE TABLE IF NOT EXISTS stats_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    login_id     INTEGER,
    app_id       INTEGER,
    package      TEXT,
    product_name TEXT,
    role_name    TEXT,
    device       TEXT,
    cpu          TEXT,
    gpu          TEXT,
    memory       INTEGER,
    gpu_memory   INTEGER,
    stats_time   INTEGER,
    created_at   INTEGER
);


-- Index: idx_logs_create_at
DROP INDEX IF EXISTS idx_logs_create_at;

CREATE INDEX IF NOT EXISTS idx_logs_create_at ON logs (
    create_at
);


-- Index: idx_logs_log_time
DROP INDEX IF EXISTS idx_logs_log_time;

CREATE INDEX IF NOT EXISTS idx_logs_log_time ON logs (
    log_time
);


-- Index: idx_role_name_message
DROP INDEX IF EXISTS idx_role_name_message;

CREATE INDEX IF NOT EXISTS idx_role_name_message ON logs (
    role_name,
    log_message
);


-- Index: idx_stats_infos_created_at
DROP INDEX IF EXISTS idx_stats_infos_created_at;

CREATE INDEX IF NOT EXISTS idx_stats_infos_created_at ON stats_infos (
    created_at
);


-- Index: idx_stats_infos_login_id
DROP INDEX IF EXISTS idx_stats_infos_login_id;

CREATE INDEX IF NOT EXISTS idx_stats_infos_login_id ON stats_infos (
    login_id
);


-- Index: idx_stats_records_created_at
DROP INDEX IF EXISTS idx_stats_records_created_at;

CREATE INDEX IF NOT EXISTS idx_stats_records_created_at ON stats_records (
    created_at
);


-- Index: idx_stats_records_login_id
DROP INDEX IF EXISTS idx_stats_records_login_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_records_login_id ON stats_records (
    login_id
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
