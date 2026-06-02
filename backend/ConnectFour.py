import numpy as np
from Player import AIPlayer, RandomPlayer, HumanPlayer


class Game:
    def __init__(self, player1, player2, id):
        self.id = id
        self.player1 = player1
        self.player2 = player2
        self.colors = ['yellow', 'red']
        self.current_turn = 1
        self.board = np.zeros([6,7]).astype(np.uint8)
        self.game_over = False
        self.winner = None

        self.ai_players={}

        if(self.player1=="ai"):
            self.ai_players[1]= AIPlayer(1)
        if(self.player2=="ai"):
            self.ai_players[2]= AIPlayer(2)

    def serialize(self):
        return {
            "board": self.board.tolist(),
            "turn": self.current_turn,
            "winner": self.winner,
            "current_turn": self.current_turn,
            "game_over": self.game_over
        }
            
    def apply_move(self, col):

        if not self.game_over:

            if col<0 or col>6:
                return False

            if(self.update_board(col, self.current_turn)):

                if(self.game_completed(self.current_turn)):
                    self.winner= self.current_turn
                    self.game_over= True
                elif not any(0 in self.board[:, col] for col in range(self.board.shape[1])):
                    # Board is completely full with no winner, it's a draw
                    self.game_over = True
                else:
                    self.current_turn= 3-self.current_turn
                
                return True
            else:
                return False
        else:
            return False

    def update_board(self, move, player_num):
        if 0 in self.board[:,move]:
            update_row = -1
            for row in range(1, self.board.shape[0]):
                update_row = -1
                if self.board[row, move] > 0 and self.board[row-1, move] == 0:
                    update_row = row-1
                elif row==self.board.shape[0]-1 and self.board[row, move] == 0:
                    update_row = row

                if update_row >= 0:
                    self.board[update_row, move] = player_num
                    break
            
            return True
        else:
            return False


    def game_completed(self, player_num):
        player_win_str = '{0}{0}{0}{0}'.format(player_num)
        board = self.board
        to_str = lambda a: ''.join(a.astype(str))

        def check_horizontal(b):
            for row in b:
                if player_win_str in to_str(row):
                    return True
            return False

        def check_verticle(b):
            return check_horizontal(b.T)

        def check_diagonal(b):
            for op in [None, np.fliplr]:
                op_board = op(b) if op else b
                
                root_diag = np.diagonal(op_board, offset=0).astype(np.int64)
                if player_win_str in to_str(root_diag):
                    return True

                for i in range(1, b.shape[1]-3):
                    for offset in [i, -i]:
                        diag = np.diagonal(op_board, offset=offset)
                        diag = to_str(diag.astype(np.int64))
                        if player_win_str in diag:
                            return True

            return False

        return (check_horizontal(board) or
                check_verticle(board) or
                check_diagonal(board))
    
    def restart(self):
        self.board.fill(0)
        self.current_turn=1
        self.game_over=False
        self.winner=None

