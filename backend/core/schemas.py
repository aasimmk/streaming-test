from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(User):
    id: int
    created_at: datetime
