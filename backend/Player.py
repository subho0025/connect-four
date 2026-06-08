import numpy as np
import math
import time

class AIPlayer:
    def __init__(self, player_number, maxTime):
        self.player_number = player_number
        self.type = 'ai'
        self.player_string = 'Player {}:ai'.format(player_number)
        self.maxTime = maxTime
        self.startTime= 0

    def get_valid_moves(self, board):
        valid = []
        optimal = [3,2,4,1,5,0,6]
        for i in optimal:
            if (board[0,i]==0):
                valid.append(i)
        
        return valid
    
    def get_valid_row(self, board, col):
        for i in range(5,-1,-1):
            if (board[i,col]==0):
                return i
    
    def is_win(self, board, piece, row, col):

        #horizontal check
        for j in range(0,4):
            if (board[row,j]==piece and board[row,j+1]==piece and board[row,j+2]==piece and board[row,j+3]==piece):
                return True

        #vertical check
        for i in range(0,3):
            if (board[i,col]==piece and board[i+1,col]==piece and board[i+2,col]==piece and board[i+3,col]==piece):
                return True
                
        #positive diagonal
        if(-2<=row-col<4):
            lst = np.diagonal(board, row-col)
            for i in range(len(lst)-3):
                if (lst[i]==piece and lst[i+1]==piece and lst[i+2]==piece and lst[i+3]==piece):
                    return True
                
        #negative diagonal
        if(-2<=row+col-6<4):
            lst= np.diagonal(np.fliplr(board), row+col-6)
            for i in range(len(lst)-3):
                if (lst[i]==piece and lst[i+1]==piece and lst[i+2]==piece and lst[i+3]==piece):
                    return True

        return False
    
    def is_terminal(self, board):

        return (self.get_valid_moves(board)==[])
    
    
    def max_value(self, board, alpha, beta, depth):

        if (time.time()-self.startTime>=self.maxTime):
            raise TimeoutError
        
        if(self.is_terminal(board) or depth==0):
            return self.evaluation_function(board)
        
        val = -math.inf
        for col in self.get_valid_moves(board):
            row = self.get_valid_row(board, col)
            board[row, col]= self.player_number

            if(self.is_win(board, self.player_number, row, col)):
                val= self.evaluation_function(board)
                board[row, col]= 0
                return val
            
            val = max(val, self.min_value(board, alpha, beta, depth-1))
            board[row, col] = 0

            if (val >=beta):
                return val
            
            alpha = max(alpha, val)
        
        return val
    
    def min_value(self, board, alpha, beta, depth):

        if (time.time()-self.startTime>=self.maxTime):
            raise TimeoutError

        if(self.is_terminal(board) or depth==0):
            return self.evaluation_function(board)
        
        val = math.inf
        for col in self.get_valid_moves(board):
            row = self.get_valid_row(board, col)  
            board[row, col] = 3-self.player_number

            if(self.is_win(board, 3-self.player_number, row, col)):
                val= self.evaluation_function(board)
                board[row, col]= 0
                return val
            
            val = min(val, self.max_value(board, alpha, beta, depth-1))
            board[row, col] =0

            if(val <= alpha):
                return val
            
            beta = min(beta, val)

        return val


    def get_alpha_beta_move(self, board):
        """
        Given the current state of the board, return the next move based on
        the alpha-beta pruning algorithm

        This will play against either itself or a human player

        INPUTS:
        board - a numpy array containing the state of the board using the
                following encoding:
                - the board maintains its same two dimensions
                    - row 0 is the top of the board and so is
                      the last row filled
                - spaces that are unoccupied are marked as 0
                - spaces that are occupied by player 1 have a 1 in them
                - spaces that are occupied by player 2 have a 2 in them

        RETURNS:
        The 0 based index of the column that represents the next move
        """

        valid_cols = self.get_valid_moves(board)

        best_col = valid_cols[0]
        temp = board.copy()

        self.startTime = time.time()
        depth=4

        try:
            while(time.time()-self.startTime<self.maxTime):
                curr_best_val = -math.inf
                curr_best_col = valid_cols[0]

                for col in valid_cols:
                    row = self.get_valid_row(board, col)
                    temp[row, col]=self.player_number

                    if(self.is_win(temp, self.player_number, row, col)):
                        temp[row, col]=0
                        return col
                    
                    val = self.min_value(temp, -math.inf, math.inf, depth-1)
                    temp[row,col]=0

                    if(val>curr_best_val):
                        curr_best_val = val
                        curr_best_col = col

                best_col = curr_best_col  
                depth+=1
            
        except TimeoutError:
            pass
        
        return best_col
    
    def exp_max_value(self, board, depth):

        if (time.time()-self.startTime>=self.maxTime):
            raise TimeoutError

        if(self.is_terminal(board) or depth==0):
            return self.evaluation_function(board)
        
        val = -math.inf
        for col in self.get_valid_moves(board):
            row = self.get_valid_row(board, col)
            board[row, col]=self.player_number

            if(self.is_win(board, self.player_number, row, col)):
                val= self.evaluation_function(board)
                board[row, col]= 0
                return val
            
            val = max(val, self.exp_chance_value(board, depth-1))
            board[row, col]=0
        
        return val
    
    def exp_chance_value(self, board, depth):

        if (time.time()-self.startTime>=self.maxTime):
            raise TimeoutError

        if(self.is_terminal(board) or depth==0):
            return self.evaluation_function(board)
        
        valid_cols = self.get_valid_moves(board)

        prob = 1/ len(valid_cols)

        total_score = 0

        for col in valid_cols:
            row = self.get_valid_row(board, col)
            board[row, col] = 3 - self.player_number

            if(self.is_win(board, 3-self.player_number, row, col)):
                score = self.evaluation_function(board)
            else:
                score = self.exp_max_value(board, depth-1)

            board[row, col]=0
            total_score += prob * score
        
        return total_score

    def get_expectimax_move(self, board):
        """
        Given the current state of the board, return the next move based on
        the expectimax algorithm.

        This will play against the random player, who chooses any valid move
        with equal probability

        INPUTS:
        board - a numpy array containing the state of the board using the
                following encoding:
                - the board maintains its same two dimensions
                    - row 0 is the top of the board and so is
                      the last row filled
                - spaces that are unoccupied are marked as 0
                - spaces that are occupied by player 1 have a 1 in them
                - spaces that are occupied by player 2 have a 2 in them

        RETURNS:
        The 0 based index of the column that represents the next move
        """

        valid_cols = self.get_valid_moves(board)

        best_col = valid_cols[0]
        temp = board.copy()

        self.startTime=time.time()
        depth=3

        try:
            while(time.time()-self.startTime<self.maxTime):

                curr_best_val = -math.inf
                curr_best_col = valid_cols[0]

                for col in valid_cols:
                    row = self.get_valid_row(temp, col)
                    temp[row, col] =self.player_number

                    if(self.is_win(temp, self.player_number, row, col)):
                        temp[row, col]=0
                        return col
                    val = self.exp_chance_value(temp, depth-1)
                    temp[row, col]=0

                    if(val>curr_best_val):
                        curr_best_val = val
                        curr_best_col = col
                
                best_col = curr_best_col
                depth+=1
        except TimeoutError:
            pass
        
        return best_col


    def evaluate_score(self, numZero, numPl, numOp):

        score =0

        if(numPl==4):
            score += 10000
        elif(numPl==3 and numZero==1):
            score +=10
        elif(numPl==2 and numZero==2):
            score +=5

        if(numOp==4):
            score -=10000
        elif(numOp==3 and numZero==1):
            score -= 80

        return score
    
    def evaluate_windows(self, lst,piece):

        score = 0
        
        numZero =0
        numPl=0
        numOp=0

        for i in range(0,4):
            if(lst[i]==0):
                numZero+=1
            elif(lst[i]==piece):
                numPl+=1
            else:
                numOp+=1
        
        score += self.evaluate_score(numZero, numPl, numOp)

        for i in range(4, len(lst)):
            if(lst[i]==0):
                numZero+=1
            elif(lst[i]==piece):
                numPl+=1
            else:
                numOp+=1

            if(lst[i-4]==0):
                numZero-=1
            elif(lst[i-4]==piece):
                numPl-=1
            else:
                numOp-=1

            score += self.evaluate_score(numZero, numPl, numOp)

        return score


    def evaluation_function(self, board):
        """
        Given the current stat of the board, return the scalar value that 
        represents the evaluation function for the current player
       
        INPUTS:
        board - a numpy array containing the state of the board using the
                following encoding:
                - the board maintains its same two dimensions
                    - row 0 is the top of the board and so is
                      the last row filled
                - spaces that are unoccupied are marked as 0
                - spaces that are occupied by player 1 have a 1 in them
                - spaces that are occupied by player 2 have a 2 in them

        RETURNS:
        The utility value for the current board
        """

        totalScore =0

        #horizontal scores
        for i in range(0,6):
            lst = list(board[i,:])
            totalScore += self.evaluate_windows(lst, self.player_number)

        #vertical scores
        for i in range(0,7):
            lst = list(board[:,i])
            totalScore += self.evaluate_windows(lst, self.player_number)
                
        #positive diagonal
        for i in range(-2, 4):
            lst = np.diagonal(board, i)
            totalScore += self.evaluate_windows(lst, self.player_number)
                
        #negative diagonal
        for i in range(-2, 4):
            lst = np.diagonal(np.fliplr(board), i)
            totalScore += self.evaluate_windows(lst, self.player_number)
       
        return totalScore


class RandomPlayer:
    def __init__(self, player_number):
        self.player_number = player_number
        self.type = 'random'
        self.player_string = 'Player {}:random'.format(player_number)

    def get_move(self, board):
        """
        Given the current board state select a random column from the available
        valid moves.

        INPUTS:
        board - a numpy array containing the state of the board using the
                following encoding:
                - the board maintains its same two dimensions
                    - row 0 is the top of the board and so is
                      the last row filled
                - spaces that are unoccupied are marked as 0
                - spaces that are occupied by player 1 have a 1 in them
                - spaces that are occupied by player 2 have a 2 in them

        RETURNS:
        The 0 based index of the column that represents the next move
        """
        valid_cols = []
        for col in range(board.shape[1]):
            if 0 in board[:,col]:
                valid_cols.append(col)

        return int(np.random.choice(valid_cols))


