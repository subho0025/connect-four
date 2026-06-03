from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import secrets
from ConnectFour import Game
from ws_manager import ConnectionManager

app= FastAPI()

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
    
    if not games[id].apply_move(column):
        raise HTTPException(status_code=400, detail= "Game finished")
    
    return games[id].serialize()

@app.post("/game/{id}/ai-move")
def ai_move(id: str):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
    if games[id].current_turn not in games[id].ai_players:
        raise HTTPException(status_code=400, detail="Current Player is not AI")
    
    curr = games[id].ai_players[games[id].current_turn]
    move = curr.get_alpha_beta_move(games[id].board)
    if not games[id].apply_move(move):
          raise HTTPException(status_code=400, detail="Game finished")
    
    return games[id].serialize()
    
@app.post("/game/{id}/game-over")
def game_over(id: str):
    if id not in games:
        raise HTTPException(status_code=404, detail="Invalid game")
    
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

@app.websocket("/ws/{id}")
async def ws_endpoint(websocket: WebSocket, id: str):

    player_num = await manager.connect(id, websocket)

    if player_num is None:
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
    await websocket.send_json(message)

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
        manager.disconnect(id, player_num)
        message={
            "type":"disconnection",
            "message": f"player{player_num} left the game"
        }
        await manager.broadcast(id, message)