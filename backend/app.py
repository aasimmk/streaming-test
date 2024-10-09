import uuid
from collections import defaultdict
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime
from core import schemas, auth, models
from utils import account as account_utils
from _config import ALGORITHM, SECRET_KEY

active_connections = defaultdict(list)
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

users_db = {}
conversations_db = {}
messages_db = {}
user_id_counter = 1
conversation_id_counter = 1
message_id_counter = 1


app = FastAPI()

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GetOrCreateThreadRequest(BaseModel):
    title: str


class UserBase(BaseModel):
    username: str
    # email: EmailStr


class UserCreate(UserBase):
    password: str


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageOut(MessageBase):
    id: int
    content: str
    sender_id: str
    sender_username: str
    timestamp: datetime


class UserOut(UserBase):
    id: int
    created_at: datetime


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    participant_ids: List[int]


class ConversationOut(ConversationBase):
    id: int
    created_at: datetime
    participants: List[str]
    messages: List[MessageOut] = []


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


class ConversationParticipant(BaseModel):
    user_id: int
    conversation_id: int


@app.post("/conversations/", response_model=ConversationOut)
def create_new_conversation(
        conversation: ConversationCreate,
        current_user: dict = Depends(account_utils.get_current_user_data)
):
    global conversation_id_counter
    participants = [current_user.get("username")]
    for pid in conversation.participant_ids:
        participant = next((u for u in users_db if u.id == pid), None)
        if participant and participant not in participants:
            participants.append(participant)
    new_conversation = ConversationOut(
        id=conversation_id_counter,
        title=conversation.title,
        created_at=datetime.utcnow(),
        participants=participants,
        messages=[]
    )
    conversations_db[conversation_id_counter] = new_conversation
    conversation_id_counter += 1
    return new_conversation


@app.get("/conversations/", response_model=List[ConversationOut])
def read_user_conversations(current_user: dict = Depends(account_utils.get_current_user_data)):
    user_convs = current_user.get("conversations") or []
    convs_out = []
    for conv in user_convs:
        conv_out = ConversationOut(
            id=conv["id"],
            title=conv["title"],
            created_at=conv["created_at"],
            participants=conv.participants,
            messages=[
                MessageOut(
                    id=m["id"],
                    content=m["content"],
                    sender_id=m["sender_id"],
                    sender_username=m["sender_username"],
                    timestamp=m["timestamp"]
                ) for m in conv["messages"]
            ]
        )
        convs_out.append(conv_out)
    return convs_out


@app.get("/conversations/{conversation_id}", response_model=ConversationOut)
def read_conversation(conversation_id: int, current_user: dict = Depends(account_utils.get_current_user_data)):
    conv = conversations_db.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.get("username") not in conv.participants:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    conv_out = ConversationOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        participants=conv.participants,
        messages=[
            MessageOut(
                id=message["id"],
                content=message["content"],
                sender_id=message["sender_id"],
                sender_username=message["sender_username"],
                timestamp=message["timestamp"]
            ) for message in conv.messages
        ]
    )
    return conv_out


@app.post("/conversations/{conversation_id}/messages/", response_model=MessageOut)
def create_message_in_conversation(conversation_id: int, message: MessageCreate,
                                   current_user: dict = Depends(account_utils.get_current_user_data)):
    global message_id_counter
    conv = conversations_db.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.get("username") not in conv.participants:
        raise HTTPException(status_code=403, detail="Not authorized to send messages in this conversation")
    msg = {
        "id": message_id_counter,
        "content": message.content,
        "sender_id": current_user["username"],  # ToDo: implement user id
        "sender_username": current_user["username"],
        "timestamp": datetime.utcnow()
    }
    message_out = MessageOut(
        id=msg["id"],
        content=msg["content"],
        sender_id=msg["sender_id"],
        sender_username=msg["sender_username"],
        timestamp=msg["timestamp"]
    )
    message_id_counter += 1

    conv.messages.append(msg)
    return message_out


@app.get("/conversations/{conversation_id}/messages/", response_model=List[MessageOut])
def read_messages(conversation_id: int, current_user: dict = Depends(account_utils.get_current_user)):
    conv = conversations_db.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user not in conv["participants"]:
        raise HTTPException(status_code=403, detail="Not authorized to view messages in this conversation")
    messages_out = [
        MessageOut(
            id=m["id"],
            content=m["content"],
            sender_id=m["sender_id"],
            sender_username=m["sender_username"],
            timestamp=m["timestamp"]
        ) for m in conv["messages"]
    ]
    return messages_out


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
