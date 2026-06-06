from fastapi import WebSocket
from collections import deque
import asyncio

class ConnectionManager:
    def __init__(self):
        self.rooms = {}
        self.waiting = deque()
        self.lock = asyncio.Lock()

    async def connect(self, id: str, websocket: WebSocket):
        await websocket.accept()

        if id not in self.rooms:
            future = asyncio.Future()
            self.rooms[id]= {
                "player1": websocket,
                "player2": None,
                "confirm": future
            }
            return 1
        
        elif self.rooms[id]["player2"] is None:
            self.rooms[id]["player2"]=websocket
            return 2
        
        else:
            return None
    
    def disconnect(self, id: str, player_num: int):

        if id in self.rooms:
            self.rooms[id][f"player{player_num}"]=None
        
            if (self.rooms[id]["player1"] is None and self.rooms[id]["player2"] is None):
                del self.rooms[id]
    
    async def broadcast(self, id: str, message: dict):

        if id in self.rooms:
            for num in range(1,3):
                connection = self.rooms[id].get(f"player{num}")
                if connection is not None:
                    await connection.send_json(message)