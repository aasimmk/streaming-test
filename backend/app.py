from typing import List
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from openai import OpenAI
from pydantic import BaseModel
from datetime import datetime
from backend._config import SECRET_KEY, ALGORITHM
from backend.core.auth import verify_password, create_access_token
from backend.core.models import ReadConversation, WriteConversation, Token, MessageOut, MessageCreate, UserInDB
from backend.core.open_ai import client, EventHandler
from backend.core.simulators import conversations_db, active_websocket_connections
from backend.utils.account import get_user, get_current_user, get_current_user_data


message_id_counter = 1
conversation_id_counter = 1
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

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


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected-route")
def protected_route(token: UserInDB = Depends(get_current_user)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": f"Hello, {token.username}! This is a protected route."}


def list_threads() -> List[ReadConversation]:
    return list(conversations_db.values())


class ConversationParticipant(BaseModel):
    user_id: int
    conversation_id: int


@app.post("/conversations/", response_model=WriteConversation)
def create_new_conversation(
        conversation: ReadConversation,
        current_user: dict = Depends(get_current_user_data)
):
    global conversation_id_counter  # I know it's bad, but need for persistent behaviour for demo.

    # add other users forcefully for demo.
    participants = [current_user.get("username"), "admin", "khan"]
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
        messages=[],
        open_ai_assistant_id=assistant.id,
        open_ai_thread_id=thread.id,
    )
    conversations_db[conversation_id_counter] = new_conversation
    conversation_id_counter += 1
    return new_conversation


@app.get("/conversations/", response_model=List[WriteConversation])
def read_user_conversations(current_user: dict = Depends(get_current_user_data)):
    user_threads = [
        thread for thread in list_threads()
        if current_user["username"] in thread.participant_ids
    ]
    return user_threads


@app.get("/conversations/{conversation_id}", response_model=WriteConversation)
def read_conversation(conversation_id: int, current_user: dict = Depends(get_current_user_data)):
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
                id=message.id,
                content=message.content,
                sender_id=message.sender_id,
                sender_username=message.sender_username,
                response=message.response,
                timestamp=message.timestamp
            ) for message in conv.messages
        ]
    )
    return conversation


@app.post("/conversations/{conversation_id}/messages/", response_model=MessageOut)
def create_message_in_conversation(conversation_id: int, message: MessageCreate,
                                   current_user: dict = Depends(get_current_user_data)):
    global message_id_counter
    conv = conversations_db.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.get("username") not in conv.participant_ids:
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

    conv.messages.append(message_out)
    return message_out


@app.get("/conversations/{conversation_id}/messages/", response_model=List[MessageOut])
def read_messages(conversation_id: int, current_user: dict = Depends(get_current_user)):
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


async def broadcast(conversation_id: str, message: str):
    connections = active_websocket_connections.get(conversation_id, [])
    for connection in connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        full_text_response = ""
        try:
            prompt_data = await websocket.receive_json()
            print(f"Websocket message: {prompt_data}")
        except WebSocketException as ex:
            print("No data supplied to websocket. Closing connection.")
            await websocket.close()
            return
        try:
            token = prompt_data["access_token"]

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    await websocket.close(code=1008)
                    return
            except JWTError:
                await websocket.close(code=1008)
                return

            prompt = prompt_data["content"]
            conversation = conversations_db.get(prompt_data["conversation_id"])
            message_id = prompt_data["id"]
            message = next((msg for msg in conversation.messages if msg.id == message_id), None)

            # Add message to the openai thread
            open_ai_message = client.beta.threads.messages.create(
                thread_id=conversation.open_ai_thread_id,
                role="user",
                content=prompt,
            )
            print(open_ai_message)
            with client.beta.threads.runs.stream(
                    thread_id=conversation.open_ai_thread_id,
                    assistant_id=conversation.open_ai_assistant_id,
                    event_handler=EventHandler()
            ) as stream:
                for event in stream:
                    if event.data.object == 'thread.message.delta' and event.data.delta.content:
                        text = event.data.delta.content[0].text.value
                        full_text_response += text
                        print(text, end='', flush=True)
                        await websocket.send_text(text)
            if message:
                message.response = full_text_response
        except WebSocketDisconnect:
            await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
