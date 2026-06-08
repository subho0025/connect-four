from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import secrets
from ConnectFour import Game
from ws_manager import ConnectionManager
from collections import deque
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app= FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://phantom-connect4.vercel.app",
        "http://127.0.0.1:5500"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

@app.get("/")
def get_root():
    return {"message": "backend working"}

games = {}

class GameConfig(BaseModel):
    player1: str
    player2: str

@app.post("/game")
def game_mode(config: GameConfig):
     
    id = secrets.token_urlsafe(8)
    games[id] = Game(config.player1, config.player2, id)

    return {
        "message": f"Game created with id {id}",
        "player1": games[id].player1,
        "player2": games[id].player2,
        "id": id
    }

@app.get("/game/{id}/state")
def get_state(id: str):

    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    return games[id].serialize()

@app.post("/game/{id}/move/{column}")
def move(id:str, column: int):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
    if games[id].current_turn in games[id].ai_players :
        raise HTTPException(status_code=400, detail="Press Next AI Move")
    
    if games[id].current_turn in games[id].random_players:
        raise HTTPException(status_code=400, detail= "Press Random Move")

    if not games[id].apply_move(column):
        raise HTTPException(status_code=400, detail= "Invalid move")
    
    return games[id].serialize()

@app.post("/game/{id}/ai-move")
def ai_move(id: str):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
    if games[id].current_turn not in games[id].ai_players:
        raise HTTPException(status_code=400, detail="Current Player is not AI")
    
    curr = games[id].ai_players[games[id].current_turn]

    if (3-curr.player_number) in games[id].random_players:
        move = curr.get_expectimax_move(games[id].board)
    else:
        move = curr.get_alpha_beta_move(games[id].board)

    if not games[id].apply_move(move):
          raise HTTPException(status_code=400, detail="Game finished")
    
    return games[id].serialize()

@app.post("/game/{id}/random-move")
def random_move(id: str):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
    if games[id].current_turn not in games[id].random_players:
        raise HTTPException(status_code=400, detail="Current Player is not Random")
    
    curr = games[id].random_players[games[id].current_turn]
    move = curr.get_move(games[id].board)
    if not games[id].apply_move(move):
        raise HTTPException(status_code=400, detail="Game finished")
    
    return games[id].serialize()

@app.delete("/game/{id}/delete")
def delete_game(id: str):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
    if id in manager.rooms:
        del manager.rooms[id]
    
    if id in games:
        del games[id]

    return {"message": f"Game id {id} deleted"}

@app.post("/game/{id}/restart")
def restart_game(id: str):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
    games[id].restart()
    return games[id].serialize()

@app.websocket("/ws/find-match")
async def find_match(websocket: WebSocket):

    await websocket.accept()

    future = asyncio.Future()

    wait = False

    async with manager.lock:
        if not manager.waiting:
            manager.waiting.append({
                "websocket": websocket,
                "future": future
            })

            wait = True

        else:
            player1 = manager.waiting.popleft()
            id = secrets.token_urlsafe(8)
            games[id] = Game("human", "human", id)

            player1["future"].set_result({
                "id": id
            })

    if wait:
        try:
            info = await future
            message = {
                "type": "match found",
                **info
            }
            await websocket.send_json(message)
        except WebSocketDisconnect:
            async with manager.lock:
                manager.waiting = deque(i for i in manager.waiting if i["websocket"]!=websocket)
    else:
        message={
            "type": "match found",
            "id": id
        }
        await websocket.send_json(message)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    return

@app.websocket("/ws/{id}")
async def ws_endpoint(websocket: WebSocket, id: str):

    if id not in games:
        await websocket.accept()
        message = {
            "type": "error",
            "message": "invalid game id"
        }
        await websocket.send_json(message)
        await websocket.close()
        return

    player_num = await manager.connect(id, websocket)

    if (player_num==1):
        try:
            val = await manager.rooms[id]["confirm"]
            if not val:
                ret = {
                    "type": "error",
                    "message": "join error"
                }
                await websocket.send_json(ret)
                return
        except WebSocketDisconnect:
            manager.disconnect(id, 1)
            return

    elif (player_num==2):
        async with manager.lock:
            if not manager.rooms[id]["confirm"].done():
                manager.rooms[id]["confirm"].set_result(True)

    else:
        message = {
            "type": "error",
            "message": "room full"
        }
        await websocket.send_json(message)
        await websocket.close()
        return
    
    message = {
        "type": "join confirmation",
        "player": player_num,
        "state": games[id].serialize()
    }
    try: 
        await websocket.send_json(message)
    except (WebSocketDisconnect, RuntimeError):
        await clean_disconnect(id, player_num)
        return

    try:
        while True:
            data = await websocket.receive_json()

            if(data.get("type")=="move"):
                if (player_num != games[id].current_turn):
                    message = {
                        "type": "error",
                        "message": "wait for your turn"
                    }
                    await websocket.send_json(message)
                    continue
                
                if (games[id].apply_move(data["col"])):
                    state = {
                        "type": "state",
                        **games[id].serialize()
                    }
                    await manager.broadcast(id, state)
                else:
                    message = {
                        "type": "error",
                        "message": "invalid move"
                    }
                    await websocket.send_json(message)
            else:
                message= {
                    "type": "error",
                    "message": "invalid move"
                }
                await manager.broadcast(id, message)
    
    except WebSocketDisconnect:
        await clean_disconnect(id, player_num)


async def clean_disconnect(id: str, player_num: int):
    manager.disconnect(id, player_num)
    if id in games:
        if id in manager.rooms:
            if not games[id].game_over:
                games[id].winner = 3-player_num
                games[id].game_over = True
            message = {
                "type": "disconnection",
                "message": f"player{player_num} left the game",
                **games[id].serialize()
                }
            await manager.broadcast(id, message)

        else:
            del games[id]