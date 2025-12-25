class GameEngine:
    def __init__(self):
        self.board = [""] * 9
        self.turn = 'X'
        self.winner = None

    def reset(self):
        self.board = [""] * 9
        self.turn = 'X'
        self.winner = None

    def make_move(self, index, symbol):
        """Returns True if move is valid, False otherwise."""
        if self.board[index] == "" and self.winner is None:
            self.board[index] = symbol
            return True
        return False

    def switch_turn(self):
        self.turn = 'O' if self.turn == 'X' else 'X'

    def check_winner(self):
        """Returns (WinnerSymbol, WinningIndices) or (None, [])"""
        wins = [
            (0,1,2), (3,4,5), (6,7,8), # Rows
            (0,3,6), (1,4,7), (2,5,8), # Cols
            (0,4,8), (2,4,6)           # Diagonals
        ]
        
        for a,b,c in wins:
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] != "":
                self.winner = self.board[a]
                return self.winner, [a,b,c]
        
        if "" not in self.board:
            return "Draw", []
            
        return None, []
