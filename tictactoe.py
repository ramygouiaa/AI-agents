from tkinter import Tk, Button, messagebox

class TicTacToeGUI:
    def __init__(self):
        self.window = Tk()
        self.window.title("Tic-Tac-Toe")
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.buttons = []
        
        for i in range(3):
            row = []
            for j in range(3):
                button = Button(self.window, text='', font=('normal', 40), width=5, height=2,
                               command=lambda i=i, j=j: self.make_move(i, j))
                button.grid(row=i, column=j)
                row.append(button)
            self.buttons.append(row)
            
        reset_button = Button(self.window, text="Reset", font=('normal', 20), command=self.reset_game)
        reset_button.grid(row=3, column=0, columnspan=3, sticky="ew")
        
    def make_move(self, row, col):
        if self.board[row][col] == ' ':
            self.board[row][col] = self.current_player
            self.buttons[row][col].config(text=self.current_player)
            
            if self.check_winner(self.board, self.current_player):
                messagebox.showinfo("Game Over", f"Player {self.current_player} wins!")
                self.reset_game()
            elif self.is_draw(self.board):
                messagebox.showinfo("Game Over", "It's a draw!")
                self.reset_game()
            else:
                self.current_player = 'O' if self.current_player == 'X' else 'X'
                
    def reset_game(self):
        for i in range(3):
            for j in range(3):
                self.board[i][j] = ' '
                self.buttons[i][j].config(text='')
        self.current_player = 'X'

    def check_winner(self, board, player):
        # Check rows
        for row in board:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(board[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2 - i] == player for i in range(3)):
            return True
        return False

    def is_draw(self, board):
        return all(x != ' ' for row in board for x in row)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    game = TicTacToeGUI()
    game.run()
