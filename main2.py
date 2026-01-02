from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.usernames: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str):
        self.active_connections.append(websocket)
        self.usernames[websocket] = username
        await self.broadcast_system_message(f"{username} joined the chat")

    def disconnect(self, websocket: WebSocket):
        username = self.usernames.get(websocket, "Someone")
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.usernames:
            del self.usernames[websocket]
        return username
    
    async def broadcast_chat_message(self, username: str, message:str):
        data={
            "type": "chat",
            "username": username,
            "message": message,
        }
        for connection in self.active_connections:
            await connection.send_json(data)

    async def broadcast_system_message(self, message: str):
        data={
            "type": "system",
            "message": message,
        }
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

@app.get("/")
async def get():
    return{"message": "Chatterbox Milestone 2 - Websocket chat server is running."}

@app.websocket("/ws")
async def web_socket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected (raw Websocket accepted)")

    username="Anonymous"

    try:
        join_data = await websocket.receive_json()
        if join_data.get("type") == "join":
            username = join_data.get("username", "Anonymous")
            print(f"User joined with username: {username}")
            await manager.connect(websocket, username)
        else:
            await manager.connect(websocket, username)

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                message_text = data.get("message", "").strip()
                if message_text:
                    print(f"[CHAT] {username}: {message_text}")
                    await manager.broadcast_chat_message(username, message_text)

    except WebSocketDisconnect:
        left_user = manager.disconnect(websocket)
        print(f"User disconnected: {left_user}")
        await manager.broadcast_system_message(f"{left_user} left the chat")

    except Exception as e:
        left_user = manager.disconnect(websocket)
        print("Unexpected error:, client disconnected", e)
        await manager.broadcast_system_message(f"{left_user} left the chat due to an error")

if __name__ == "__main__":
    uvicorn.run("main2:app", host="localhost", port=8000, reload=True)