import socket
import json
import threading
from client_renderer import GameRenderer

# Configuration
HOST = 'localhost'
PORT = 9999

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


def connect_to_server():
    """Create a socket connection to the server and start the receive thread.
    Returns the socket on success, or None on failure."""
    global connected, my_player_id, game_state

    my_player_id = None
    game_state = {'players': {}, 'bullets': []}

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        connected = True
        print(f"Connected to server at {HOST}:{PORT}")
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        print("Make sure the server is running: python server_main.py")
        return None

    receive_thread = threading.Thread(target=receive_data, args=(sock,), daemon=True)
    receive_thread.start()
    return sock


# Empty input sent while paused so the player doesn't move
EMPTY_INPUT = json.dumps({'w': False, 's': False, 'a': False, 'd': False, 'space': False}) + '\n'


def main():
    """Client Runner: Connect, loop, send actions, receive state, render."""
    global connected

    renderer = GameRenderer()
    sock = connect_to_server()
    if sock is None:
        renderer.quit()
        return

    running = True
    while running and connected:
        action = renderer.handle_events()
        if action == 'quit':
            running = False
            break
        if action == 'reset':
            # Close current connection and reconnect
            connected = False
            try:
                sock.close()
            except Exception:
                pass
            sock = connect_to_server()
            if sock is None:
                running = False
                break
            continue

        # When paused, send empty input so the player stands still
        if renderer.paused:
            try:
                sock.send(EMPTY_INPUT.encode())
            except Exception:
                running = False
                break
        else:
            inputs = renderer.get_inputs()
            try:
                sock.send((json.dumps(inputs) + '\n').encode())
            except Exception as e:
                print(f"Send error: {e}")
                running = False
                break

        with lock:
            current_state = game_state.copy()

        renderer.draw(current_state, my_player_id)

    # Cleanup
    connected = False
    try:
        sock.close()
    except Exception:
        pass
    renderer.quit()
    print("Game closed")


if __name__ == '__main__':
    main()
