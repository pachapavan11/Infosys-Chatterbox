from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "ChatterBox Milestone 1 - WebSocket Server is running!"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    #Step 1: Accept the WebSocket connection
    await websocket.accept()
    print("client connected")


    #step 2 : Keep listening for messages from the client
    while True:
        try:
            message = await websocket.receive_text()
            print(f"Message received: {message}")

            #Step 3: Echo the message back to the client
            await websocket.send_text(f"server: You said --> {message}")

        except Exception as e:
            print("client disconnected", e)
            break

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000)