from typing import Optional
from pydantic import BaseModel


class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    status: str
    deadline: str
    user_id: Optional[int] = None


class CommonResponse(BaseModel):
    message: str
