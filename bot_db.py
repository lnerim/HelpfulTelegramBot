import sqlite3
from typing import Any

TABLE_GROUPS = "GROUPS"
GROUP_NUM = "num"
GROUP_ID = "id"
GROUP_STATUS = "status"

TABLE_TASKS = "TASKS"
TASK_NUM = "num"
TASK_USER_ID = "user_id"
TASK_GROUP_ID = "group_id"
TASK_DESCRIPTION = "description"
TASK_VALUE = "value"
TASK_TIME = "time"

TABLE_USERS = "USERS"
USER_ID = "user_id"
USER_GROUP = "group_id"

TABLE_REP = "REPUTATIONS"
REP_NUM_TASK = "num_task"
REP_USER_ID = "user_id"


class BotDataBase:
    def __init__(self, name: str = "bot_database.sqlite"):
        self.connection = sqlite3.connect(name, check_same_thread=False)
        self.cursor = self.connection.cursor()

        with self.connection:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_GROUPS} ("
                                f"{GROUP_NUM} INTEGER PRIMARY KEY, "
                                f"{GROUP_ID} INTEGER NOT NULL, "
                                f"{GROUP_STATUS} BLOB NOT NULL);")

        with self.connection:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_TASKS} ("
                                f"{TASK_NUM} INTEGER PRIMARY KEY, "
                                f"{TASK_USER_ID} INTEGER NOT NULL, "
                                f"{TASK_GROUP_ID} INTEGER NOT NULL, "
                                f"{TASK_DESCRIPTION} TEXT, "
                                f"{TASK_VALUE} INTEGER NOT NULL, "
                                f"{TASK_TIME} REAL NOT NULL);")

        with self.connection:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_USERS} ("
                                f"{USER_ID} INTEGER NOT NULL, "
                                f"{USER_GROUP} INTEGER NOT NULL);")

        with self.connection:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_REP} ("
                                f"{REP_NUM_TASK} INTEGER NOT NULL, "
                                f"{REP_USER_ID} INTEGER NOT NULL);")

    def group_add(self, group_id, status=True):
        with self.connection:
            self.cursor.execute(
                f"INSERT INTO `{TABLE_GROUPS}` (`{GROUP_ID}`, `{GROUP_STATUS}`) VALUES(?,?)", (group_id, status)
            )

    def group_check(self, group_id) -> bool:
        with self.connection:
            result = self.cursor.execute(
                f"SELECT * FROM `{TABLE_GROUPS}` WHERE `{GROUP_ID}` = ?", (group_id,)
            ).fetchone()
            return bool(result)

    def group_update(self, group_id, status=True):
        with self.connection:
            self.cursor.execute(
                f"UPDATE `{TABLE_GROUPS}` SET `{GROUP_STATUS}` = ? WHERE `{GROUP_ID}` = ?", (status, group_id)
            )

    def groups_by_status(self, status=True) -> list[Any]:
        with self.connection:
            return self.cursor.execute(
                f"SELECT * FROM `{TABLE_GROUPS}` WHERE `{GROUP_STATUS}` = ?", (status,)
            ).fetchall()

    def task_add(self, user_id, group_id, description, time) -> tuple[int, float]:
        with self.connection:
            self.cursor.execute(
                f"INSERT INTO `{TABLE_TASKS}` "
                f"(`{TASK_USER_ID}`, `{TASK_GROUP_ID}`, `{TASK_DESCRIPTION}`, `{TASK_TIME}`, `{TASK_VALUE}`) "
                f"VALUES(?,?,?,?,?)", (user_id, group_id, description, time, 1)
            )
            return self.cursor.lastrowid, time

    def task_update(self, task_id, value):
        with self.connection:
            self.cursor.execute(
                f"UPDATE `{TABLE_TASKS}` SET `{TASK_VALUE}` = `{TASK_VALUE}` + ? WHERE `{TASK_NUM}` = ?",
                (value, task_id)
            )

    # Возможно больше не будет нужно
    def tasks_by_time(self, user_id, group_id, time_start, time_end) -> list[Any]:
        with self.connection:
            return self.cursor.execute(
                f"SELECT * FROM `{TABLE_TASKS}` WHERE `{TASK_USER_ID}` = ? AND `{TASK_GROUP_ID}` = ? AND "
                f"`{TASK_TIME}` >= ? AND `{TASK_TIME}` < ?",
                (user_id, group_id, time_start, time_end)
            ).fetchall()

    def value_by_time(self, user_id, group_id, time_start, time_end) -> int:
        with self.connection:
            result = self.cursor.execute(
                f"SELECT SUM({TASK_VALUE}) FROM `{TABLE_TASKS}` "
                f"WHERE `{TASK_USER_ID}` = ? AND `{TASK_GROUP_ID}` = ? AND "
                f"`{TASK_TIME}` >= ? AND `{TASK_TIME}` < ?",
                (user_id, group_id, time_start, time_end)
            ).fetchone()
        result = result[0]
        return result if result is not None else 0

    def user_remember(self, user_id, group_id):
        with self.connection:
            result = self.cursor.execute(
                f"SELECT * FROM `{TABLE_USERS}` WHERE `{USER_ID}` = ? AND `{USER_GROUP}` = ?",
                (user_id, group_id)
            ).fetchone()
            if not result:
                self.cursor.execute(
                    f"INSERT INTO `{TABLE_USERS}` (`{USER_ID}`, `{USER_GROUP}`) VALUES(?,?)", (user_id, group_id)
                )

    def users_by_group(self, group_id) -> tuple[Any]:
        with self.connection:
            result = self.cursor.execute(
                f"SELECT {USER_ID} FROM `{TABLE_USERS}` WHERE `{USER_GROUP}` = ?", (group_id,)
            ).fetchall()
            return tuple(elem[0] for elem in result)

    def rep_add(self, num_task, user_id):
        with self.connection:
            self.cursor.execute(
                f"INSERT INTO `{TABLE_REP}` (`{REP_NUM_TASK}`, `{REP_USER_ID}`) VALUES(?,?)", (num_task, user_id)
            )

    def rep_check(self, num_task, user_id) -> bool:
        with self.connection:
            result = self.cursor.execute(
                f"SELECT * FROM `{TABLE_REP}` WHERE `{REP_NUM_TASK}` = ? AND `{REP_USER_ID}` = ?", (num_task, user_id)
            ).fetchone()
            return bool(result)

    def rep_delete(self, num_task, user_id):
        with self.connection:
            self.cursor.execute(
                f"DELETE FROM `{TABLE_REP}` WHERE `{REP_NUM_TASK}` = ? AND `{REP_USER_ID}` = ?", (num_task, user_id)
            )


if __name__ == '__main__':
    BotDataBase(":memory:")
