import uuid
from collections import defaultdict
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from core import schemas, auth, models
from utils import account as account_utils
from _config import ALGORITHM, SECRET_KEY

active_connections = defaultdict(list)
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app = FastAPI()

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = account_utils.get_user(form_data.username)
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# Protected route example
@app.get("/protected-route")
def protected_route(token: models.UserInDB = Depends(account_utils.get_current_user)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": f"Hello, {token.username}! This is a protected route."}


class ConversationThread(BaseModel):
    id: str
    title: str
    participants: List[str]


class CreateThreadRequest(BaseModel):
    title: str


class AddParticipantRequest(BaseModel):
    username: str

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


def get_or_create_thread(title: str, username: str) -> ConversationThread:
    for thread in threads_db.values():
        if thread.title == title and username in thread.participants:
            return thread
    return create_new_thread(title, username)


@app.get("/threads", response_model=List[ConversationThread])
async def list_conversation_threads(current_user: models.UserInDB = Depends(account_utils.get_current_user)):
    user_threads = [
        thread for thread in list_threads()
        if current_user.username in thread.participants
    ]
    return user_threads


@app.post("/threads", response_model=ConversationThread)
async def create_conversation_thread(
        request: CreateThreadRequest,
        current_user: models.UserInDB = Depends(account_utils.get_current_user)):
    thread = create_new_thread(title=request.title, creator_username=current_user.username)
    return thread


class GetOrCreateThreadRequest(BaseModel):
    title: str


@app.post("/threads/get_or_create", response_model=ConversationThread)
async def get_or_create_conversation_thread(request: GetOrCreateThreadRequest,
                                            current_user: models.UserInDB = Depends(account_utils.get_current_user)):
    thread = get_or_create_thread(title=request.title, username=current_user.username)
    return thread


@app.post("/threads/{thread_id}/add", response_model=ConversationThread)
async def add_participant_to_thread(thread_id: str, request: AddParticipantRequest,
                                    current_user: models.UserInDB = Depends(account_utils.get_current_user)):
    thread = get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    if current_user.username not in thread.participants:
        raise HTTPException(status_code=403, detail="Not authorized to modify this thread")
    add_participant(thread_id, request.username)
    return thread


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    user = account_utils.get_user(username=username)
    if user is None:
        await websocket.close(code=1008)
        return

    thread = get_thread(thread_id)
    if thread is None:
        await websocket.close(code=1008)
        return

    if username not in thread.participants:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    active_connections[thread_id].append(websocket)
    await broadcast(thread_id, f"{username} has connected.")

    try:
        while True:
            data = await websocket.receive_text()
            message = f"{username}: {data}"
            await broadcast(thread_id, message)
    except WebSocketDisconnect:
        active_connections[thread_id].remove(websocket)
        await broadcast(thread_id, f"{username} has disconnected.")
    except Exception as e:
        active_connections[thread_id].remove(websocket)
        await broadcast(thread_id, f"{username} has left the chat due to an error.")
        print(f"Connection error: {e}")


async def broadcast(thread_id: str, message: str):
    connections = active_connections.get(thread_id, [])
    for connection in connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")


class AddParticipantRequest(BaseModel):
    username: str


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
