# db.py
import psycopg2

import models

# Одно подключение на всё приложение (для продакшена так не делаем, но для учебного норм)
conn = psycopg2.connect(
    dbname="alif_todo_list",
    host="localhost",
    user="postgres",
    password="postgres",
    port="5432",
)
conn.autocommit = True


def create_user(full_name: str, username: str, password_hash: str):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (full_name, username, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, password_hash
            """,
            (full_name, username, password_hash),
        )
        return cursor.fetchone()  # (id, username, password_hash)

# функция для получения пользователя из БД по username
def get_user_by_username(username: str):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        )
        return cursor.fetchone()  # или None


def create_task(task: models.Task):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tasks (title, description, status, deadline, user_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (task.title, task.description, task.status, task.deadline, task.user_id),
        )


def get_all_tasks(user_id: int, status_filter: str | None, sort_column: str | None):
    sql = "SELECT id, title, description, status, deadline, user_id FROM tasks WHERE user_id = %s"
    params: list = [user_id]

    if status_filter is not None:
        sql += " status = %s"
        params.append(status_filter)

    # Белый список для сортировки, чтобы не было SQL-инъекций
    allowed_sort_columns = {"id", "title", "status", "deadline"}
    if sort_column not in allowed_sort_columns:
        sort_column = "id"

    sql += f" ORDER BY {sort_column}"

    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        tasks: list[models.Task] = []
        for row in cursor.fetchall():
            tasks.append(
                models.Task(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    status=row[3],
                    deadline=str(row[4]),
                    user_id=str(row[5]),
                )
            )
        return tasks


def get_task_by_id(task_id: int) -> models.Task | None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, title, description, status, deadline, user_id FROM tasks WHERE id = %s",
            (task_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return models.Task(
            id=row[0],
            title=row[1],
            description=row[2],
            status=row[3],
            deadline=str(row[4]),
            user_id=row[5],
        )


def update_task(task: models.Task):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET title = %s,
                description = %s,
                status = %s,
                deadline = %s
            WHERE id = %s AND user_id = %s
            """,
            (task.title, task.description, task.status, task.deadline, task.id, task.user_id),
        )


def delete_task(user_id: int, task_id: int):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
