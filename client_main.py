import socket
import json
import threading
from client_renderer import GameRenderer

# Configuration
HOST = 'localhost'
PORT = 21001

# Game state (shared between threads)
game_state = {'players': {}, 'bullets': []}
my_player_id = None
lock = threading.Lock()
connected = False


def receive_data(sock):
    """Background thread to receive state from server."""
    global game_state, my_player_id, connected

    buffer = ""
    while connected:
        try:
            data = sock.recv(4096).decode()
            if not data:
                connected = False
                break

            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line:
                    try:
                        msg = json.loads(line)
                        if msg.get('type') == 'init':
                            my_player_id = msg['id']
                            print(f"Connected as Player {my_player_id} ({msg.get('color', 'unknown')})")
                        elif msg.get('type') == 'state':
                            with lock:
                                game_state = msg
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"Receive error: {e}")
            connected = False
            break


def main():
    """Client Runner: Connect, loop, send actions, receive state, render."""
    global connected

    # Initialize renderer
    renderer = GameRenderer()

    # Connect to localhost:21001
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        connected = True
        print(f"Connected to server at {HOST}:{PORT}")
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        print("Make sure the server is running: python server_main.py")
        renderer.quit()
        return

    # Start receive thread
    receive_thread = threading.Thread(target=receive_data, args=(sock,), daemon=True)
    receive_thread.start()

    # Main game loop
    running = True
    while running and connected:
        # Handle pygame events (quit, etc.)
        if not renderer.handle_events():
            running = False
            break

        # Get keys (WASD + Space)
        inputs = renderer.get_inputs()

        # Send actions to server
        try:
            sock.send((json.dumps(inputs) + '\n').encode())
        except Exception as e:
            print(f"Send error: {e}")
            running = False
            break

        # Receive state (handled by background thread)
        # Get current state safely
        with lock:
            current_state = game_state.copy()

        # Call renderer.draw(state)
        renderer.draw(current_state, my_player_id)

    # Cleanup
    connected = False
    try:
        sock.close()
    except:
        pass
    renderer.quit()
    print("Game closed")


if __name__ == '__main__':
    main()
