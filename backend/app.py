from collections import defaultdict
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from openai import OpenAI
from pydantic import BaseModel
from datetime import datetime

from backend.open_ai import client
from core import schemas, auth, models
from utils import account as account_utils

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
threads_db = {}

app = FastAPI()
openai_client = OpenAI()

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
    response: Optional[str]
    timestamp: datetime


class UserOut(UserBase):
    id: int
    created_at: datetime


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


def list_threads() -> List[ReadConversation]:
    return list(conversations_db.values())


# def add_participant(thread_id: str, username: str):
#     thread = conversations_db.get(thread_id)
#     if thread and username not in thread.participants:
#         thread.participants.append(username)


class ConversationParticipant(BaseModel):
    user_id: int
    conversation_id: int


@app.post("/conversations/", response_model=WriteConversation)
def create_new_conversation(
        conversation: ReadConversation,
        current_user: dict = Depends(account_utils.get_current_user_data)
):
    global conversation_id_counter
    participants = [current_user.get("username")]
    for pid in conversation.participant_ids:
        participant = next((u for u in users_db if u.id == pid), None)
        if participant and participant not in participants:
            participants.append(participant)
            # add other users forcefully
            participant.extend(["admin", "khan"])

    assistant = client.beta.assistants.create(
        instructions="You are a weather bot. Use the provided functions to answer questions.",
        model="gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_current_temperature",
                    "description": "Get the current temperature for a specific location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g., San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["Celsius", "Fahrenheit"],
                                "description": "The temperature unit to use. Infer this from the user's location."
                            }
                        },
                        "required": ["location", "unit"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_rain_probability",
                    "description": "Get the probability of rain for a specific location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g., San Francisco, CA"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
    )
    thread = client.beta.threads.create()

    new_conversation = WriteConversation(
        id=conversation_id_counter,
        title=conversation.title,
        created_at=datetime.utcnow(),
        participant_ids=participants,
        open_ai_assistant_id=assistant.id,
        open_ai_thread_id=thread.id,
    )
    conversations_db[conversation_id_counter] = new_conversation
    conversation_id_counter += 1
    return new_conversation


@app.get("/conversations/", response_model=List[WriteConversation])
def read_user_conversations(current_user: dict = Depends(account_utils.get_current_user_data)):
    user_threads = [
        thread for thread in list_threads()
        if current_user["username"] in thread.participant_ids
    ]
    return user_threads


@app.get("/conversations/{conversation_id}", response_model=WriteConversation)
def read_conversation(conversation_id: int, current_user: dict = Depends(account_utils.get_current_user_data)):
    conv = conversations_db.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.get("username") not in conv.participant_ids:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    conversation = WriteConversation(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        participant_ids=conv.participant_ids,
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
    return conversation


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
        response="",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
