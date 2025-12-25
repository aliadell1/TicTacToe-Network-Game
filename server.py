import socket
import threading

HOST = '0.0.0.0'
PORT = 5555

clients = {}       # {username: client_socket}
client_games = {}  # {username: opponent_username}

def broadcast_player_list():
    """Sends the list of active players to everyone."""
    active_players = [u for u in clients.keys()]
    player_list = "LIST," + ",".join(active_players)
    print(f"Server: broadcasting players -> {active_players}")
    for client_sock in list(clients.values()):
        try:
            client_sock.sendall(player_list.encode('utf-8'))
        except Exception as e:
            print(f"Server: failed to send player list to a client: {e}")

def handle_client(client_socket):
    username = None
    try:
        username = client_socket.recv(1024).decode('utf-8')
        if username in clients:
            client_socket.send("ERROR:Name taken".encode('utf-8'))
            client_socket.close()
            return

        clients[username] = client_socket
        print(f"Server: {username} connected.")
        broadcast_player_list()

        while True:
            msg = client_socket.recv(1024).decode('utf-8')
            if not msg: break

            if msg.startswith("INVITE:"):
                target = msg.split(":")[1]
                if target in clients:
                    clients[target].send(f"INVITE_FROM:{username}".encode('utf-8'))
            
            elif msg.startswith("ACCEPT:"):
                challenger = msg.split(":")[1]
                client_games[username] = challenger
                client_games[challenger] = username
                # Start Game (Challenger is X, Accepter is O)
                clients[username].send(f"GAME_START:YOU_O:{challenger}".encode('utf-8'))
                clients[challenger].send(f"GAME_START:YOU_X:{username}".encode('utf-8'))

            elif msg.startswith("MOVE:"):
                move_idx = msg.split(":")[1]
                opponent = client_games.get(username)
                if opponent:
                    clients[opponent].send(f"OPPONENT_MOVE:{move_idx}".encode('utf-8'))

    except Exception as e:
        print(f"Error ({username}): {e}")
    finally:
        if username in clients:
            del clients[username]
            opponent = client_games.get(username)
            if opponent and opponent in clients:
                clients[opponent].send("OPPONENT_LEFT".encode('utf-8'))
                del client_games[username]
                if opponent in client_games: del client_games[opponent]
            broadcast_player_list()
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"--- Server Running on {HOST}:{PORT} ---")
    
    while True:
        client_sock, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock,))
        thread.start()

if __name__ == "__main__":
    start_server()
