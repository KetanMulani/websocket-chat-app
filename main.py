from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from cryptography.fernet import Fernet

app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

rooms = {}
room_keys = {}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):

    username = websocket.query_params.get("username")

    if not username:
        await websocket.close()
        return

    await websocket.accept()

    if room_id not in rooms:
        rooms[room_id] = {}
        room_keys[room_id] = Fernet.generate_key()

    if username in rooms[room_id]:
        await websocket.send_text("Username already taken")
        await websocket.close()
        return

    if len(rooms[room_id]) >= 4:
        await websocket.send_text("Room is full (max 4 users)")
        await websocket.close()
        return

    rooms[room_id][username] = websocket
    print(f"{username} joined room {room_id}")

    cipher = Fernet(room_keys[room_id])

    for user_ws in rooms[room_id].values():
        await user_ws.send_text(f"{username} joined the room")

    try:
        while True:

            message = await websocket.receive_text()

            encrypted_message = cipher.encrypt(message.encode())

            decrypted_message = cipher.decrypt(encrypted_message).decode()

            for user_ws in rooms[room_id].values():
                await user_ws.send_text(f"{username}: {decrypted_message}")

    except WebSocketDisconnect:
    
        del rooms[room_id][username]
        print(f"{username} left room {room_id}")

        
        for user_ws in rooms[room_id].values():
            await user_ws.send_text(f"{username} left the room")

        if len(rooms[room_id]) == 0:
            del rooms[room_id]
            del room_keys[room_id]
