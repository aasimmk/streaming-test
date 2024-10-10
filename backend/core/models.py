from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class UserOut(User):
    id: int
    created_at: datetime


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageOut(MessageBase):
    id: int
    content: str
    sender_id: str
    sender_username: str
    response: Optional[str]
    timestamp: datetime


class ConversationBase(BaseModel):
    title: str
    participant_ids: List[str]


class ReadConversation(ConversationBase):
    pass


class WriteConversation(ConversationBase):
    id: int
    created_at: datetime
    messages: List[MessageOut] = []
    open_ai_assistant_id: Optional[str] = None
    open_ai_thread_id: Optional[str] = None


# in-memory users
mock_users = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$HczoMwCRPLPi/ipSquWA5OdeQ7APGRbY0u1fVv1RSAou7ALG28b.W"  # hashed "123"
    },
    "aasim": {
        "username": "aasim",
        "hashed_password": "$2b$12$HczoMwCRPLPi/ipSquWA5OdeQ7APGRbY0u1fVv1RSAou7ALG28b.W"  # hashed "123"
    },
    "dummy": {
        "username": "dummy",
        "hashed_password": "$2b$12$HczoMwCRPLPi/ipSquWA5OdeQ7APGRbY0u1fVv1RSAou7ALG28b.W"  # hashed "123"
    }
}
