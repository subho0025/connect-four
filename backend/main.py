from fastapi import FastAPI
from ConnectFour import Game
from Player import AIPlayer, RandomPlayer, HumanPlayer

game= Game()
ai= AIPlayer()
app= FastAPI()

@app.get("/")
def get_root():
    return {"message": "backend working"}

@app.state("/state")
def get_state():
    return game.serialize()

@app.post("/move/{column}")
def move(column: int):
    game.get_move(column)

@app.post("/move/ai-move")
def ai_move():
    move = ai.get_alpha_beta_move(game.board)
    game.get_move(move)