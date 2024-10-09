from typing import Dict, List, Optional
import uuid

from pydantic import BaseModel


class ConversationThread(BaseModel):
    id: str
    title: str
    participants: List[str]


class CreateThreadRequest(BaseModel):
    title: str


class UserInDB(BaseModel):
    username: str
    hashed_password: str


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

# In-memory storage for conversation threads
threads_db: Dict[str, ConversationThread] = {}


def create_new_thread(title: str, creator_username: str) -> ConversationThread:
    thread_id = str(uuid.uuid4())
    thread = ConversationThread(
        id=thread_id,
        title=title,
        participants=[creator_username]
    )
    threads_db[thread_id] = thread
    return thread


def get_thread(thread_id: str) -> Optional[ConversationThread]:
    return threads_db.get(thread_id)


def list_threads() -> List[ConversationThread]:
    return list(threads_db.values())


def add_participant(thread_id: str, username: str):
    thread = threads_db.get(thread_id)
    if thread and username not in thread.participants:
        thread.participants.append(username)
