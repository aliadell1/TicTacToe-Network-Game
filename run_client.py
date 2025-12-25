import tkinter as tk
from tkinter import simpledialog, messagebox
import socket
import threading

from game_engine import GameEngine
from ui_layout import GameUI

class MainController:
    def __init__(self, root):
        self.root = root
        self.engine = GameEngine()
        self.ui = GameUI(root, self.handle_click, self.send_invite, self.connect_mode)
        
        self.client_socket = None
        self.mode = "LOCAL" 
        self.username = ""
        self.my_symbol = 'X'
        self.running = True

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect_mode(self, mode):
        if mode == "LOCAL":
            self.mode = "LOCAL"
            self.engine.reset()
            self.ui.reset_board_visuals()
            self.ui.show_game()
            self.ui.status_label.config(text="Local Game: X's Turn")
        else:
            self.setup_network()

    
    def setup_network(self):
        def on_user_entered(name):
            self.username = name
            self.ui.create_popup("Server IP", "Enter the Server IP Address:", mode="INPUT", 
                                 callback=on_ip_entered)

        def on_ip_entered(ip):
            if not ip: ip = "localhost"
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((ip, 5555))
                # Start the receiver first to avoid missing any immediate broadcasts
                threading.Thread(target=self.receive_messages, daemon=True).start()
                # Use sendall to ensure full data is sent
                self.client_socket.sendall(self.username.encode('utf-8'))
                
                self.ui.show_lobby()
                self.ui.status_label.config(text=f"Connected as {self.username}")
            except Exception as e:
                self.ui.create_popup("Error", f"Connection Failed:\n{e}", mode="INFO")

        self.ui.create_popup("Login", "Choose a Username:", mode="INPUT", callback=on_user_entered)

    def send_invite(self, target_name):
        if self.client_socket:
            try:
                self.client_socket.sendall(f"INVITE:{target_name}".encode('utf-8'))
            except Exception:
                pass

    def handle_click(self, index, is_remote=False):
            # 1. Validation
            if self.mode == "ONLINE" and not is_remote and self.engine.turn != self.my_symbol:
                return 
            
            # 2. Make Move
            if self.engine.make_move(index, self.engine.turn):
                self.ui.update_board(index, self.engine.turn)
                
                if self.mode == "ONLINE" and not is_remote:
                    try:
                        self.client_socket.sendall(f"MOVE:{index}".encode('utf-8'))
                    except Exception:
                        pass

                # 3. Check Win
                winner, indices = self.engine.check_winner()
                
                if winner:
                    # --- GAME OVER ---
                    video_to_play = None
                    message_text = ""
                    
                    if winner == "Draw":
                        message_text = "It's a Draw!"
                        video_to_play = "draw"  # Will play 'draw.mp4' + 'draw.wav'
                    else:
                        self.ui.highlight_win(indices)
                        message_text = f"The winner is {winner}!"
                        
                        # Play 'win' only if the winner matches this client's symbol.
                        # Otherwise play 'lose' (for online games where opponent won).
                        if winner == self.my_symbol:
                            video_to_play = "win" # Will play 'win.mp4' + 'win.wav'
                        else:
                            video_to_play = "lose" # Will play 'lose.mp4' + 'lose.wav'

                    # Just ask for the popup. The UI handles the video/sound sync.
                    self.ui.create_popup(
                        title="Game Over", 
                        message=message_text, 
                        mode="INFO", 
                        video_file=video_to_play,
                        callback=lambda: [self.engine.reset(), self.ui.reset_board_visuals()]
                    )
                
                else:
                    self.engine.switch_turn()
                    if self.mode == "LOCAL":
                        self.ui.status_label.config(text=f"Local Game: {self.engine.turn}'s Turn")

    def receive_messages(self):
        while self.running:
            try:
                msg = self.client_socket.recv(1024).decode('utf-8')
                print(f"Client DEBUG: raw message received: {repr(msg)}")
                if not msg: break
                
                # [CHANGE] Using root.after() for thread safety
                if msg.startswith("LIST"):
                    players = msg.split(",")[1:]
                    players = [p for p in players if p != self.username]
                    self.root.after(0, lambda: self.ui.update_list(players))
                
                elif msg.startswith("INVITE_FROM"):
                    sender = msg.split(":")[1]
                    self.root.after(0, lambda s=sender: self.ask_accept(s))

                elif msg.startswith("GAME_START"):
                    parts = msg.split(":")
                    self.my_symbol = 'X' if parts[1] == 'YOU_X' else 'O'
                    self.mode = "ONLINE"
                    self.engine.reset()
                    self.root.after(0, lambda: self.start_online_game(parts[2]))

                elif msg.startswith("OPPONENT_MOVE"):
                    idx = int(msg.split(":")[1])
                    self.root.after(0, lambda: self.handle_click(idx, is_remote=True))
                
                elif msg == "OPPONENT_LEFT":
                    self.root.after(0, lambda: messagebox.showinfo("Info", "Opponent disconnected."))
                    self.root.after(0, self.ui.show_lobby)

            except:
                break
    
    # [CHANGE] Replaced system dialog with Custom Yes/No Popup
    def ask_accept(self, sender):
        def on_decision(accepted):
            if accepted:
                self.client_socket.send(f"ACCEPT:{sender}".encode('utf-8'))
        
        self.ui.create_popup("Challenge!", f"{sender} wants to play!", mode="YESNO", callback=on_decision)

    def start_online_game(self, opponent):
        self.ui.show_game()
        self.ui.reset_board_visuals()
        self.ui.status_label.config(text=f"Vs {opponent} | You are {self.my_symbol}")

    def on_close(self):
        self.running = False
        if self.client_socket: self.client_socket.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainController(root)
    root.mainloop()
