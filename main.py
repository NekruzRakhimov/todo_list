# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query
from pydantic import BaseModel

import db
import models
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

app = FastAPI()


@app.get("/ping")
def ping_pong():
    return {"ping": "pong"}


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/sign-up", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    existing = db.get_user_by_username(body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    password_hash = hash_password(body.password)
    db.create_user(body.full_name, body.username, password_hash)

    return models.CommonResponse(message="User created successfully")


@app.post("/auth/sign-in")
def login(body: LoginRequest):
    user = db.get_user_by_username(body.username)  # (id, username, password_hash)

    if not user or not verify_password(body.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token({"sub": user[1]})
    return {"access_token": token, "token_type": "bearer"}


# ---------- Tasks ----------

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
        task: models.Task,
        user=Depends(get_current_user),
):
    # простая валидация, можно вынести в Pydantic, но так понятнее на первом этапе
    if not task.title or not task.description or not task.status or not task.deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fill all required fields",
        )

    task.user_id = user["id"]

    db.create_task(task)
    return models.CommonResponse(message="Task created successfully")

# получение списка всех задач пользователя
@app.get("/tasks")
def get_all_tasks(
        status_filter: str | None = Query(default=None),
        sort_column: str | None = Query(default=None),
        user=Depends(get_current_user),
):
    tasks = db.get_all_tasks(user["id"], status_filter, sort_column)
    return {
        "tasks": tasks,
    }


@app.get("/tasks/{task_id}/details")
def get_task_by_id(task_id: int, user=Depends(get_current_user), ):
    task = validate_task_id(task_id)

    if task.user_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not allowed to access this task",
        )

    return {"task": task}


@app.put("/tasks/{task_id}")
def update_task(
        task_id: int,
        task: models.Task,
        user=Depends(get_current_user),
):
    task_from_db = validate_task_id(task_id)

    if task_from_db.user_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not allowed to access this task",
        )

    task.id = task_id
    task.user_id = user["id"]
    db.update_task(task)

    return models.CommonResponse(message="Task updated successfully")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, user=Depends(get_current_user)):
    task = validate_task_id(task_id)

    if task.user_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not allowed to access this task",
        )

    db.delete_task(user["id"], task_id)
    return models.CommonResponse(message="Task deleted successfully")


def validate_task_id(task_id: int) -> models.Task:
    if task_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_id must be greater than 0",
        )

    task_from_db = db.get_task_by_id(task_id)
    if task_from_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task does not exist",
        )

    return task_from_db
