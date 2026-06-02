from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ConnectFour import Game

app= FastAPI()

@app.get("/")
def get_root():
    return {"message": "backend working"}

games = {}

class GameConfig(BaseModel):
    player1: str
    player2: str
    id: str

@app.post("/game")
def game_mode(config: GameConfig):
    games[config.id] = Game(config.player1, config.player2, config.id)

    return {
        "message": f"Game created with id {config.id}",
        "player1": games[config.id].player1,
        "player2": games[config.id].player2
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
    
    del games[id]

    return {"message": f"Game id {id} deleted"}

@app.post("/game/{id}/restart")
def restart_game(id: str):
    games[id].restart()
    return games[id].serialize()