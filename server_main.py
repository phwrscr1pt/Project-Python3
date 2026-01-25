import socket
import threading
import json
import time
from game_objects import Player, Bullet

# Server configuration
HOST = '0.0.0.0'
PORT = 21001
FPS = 60
FRAME_TIME = 1 / FPS
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Game state
game_state = {
    'players': {},  # {player_id: Player object}
    'bullets': []   # [Bullet objects]
}
client_sockets = {}  # {player_id: socket}
client_inputs = {}   # {player_id: {w, a, s, d, space}}
lock = threading.Lock()
next_player_id = 0
running = True

# Player colors
COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta']


def handle_client(client_socket, player_id):
    """Handle individual client connection using threading."""
    global running

    print(f"Player {player_id} connected")

    # Send player their ID and color
    try:
        init_msg = json.dumps({
            'type': 'init',
            'id': player_id,
            'color': COLORS[player_id % len(COLORS)]
        })
        client_socket.send(init_msg.encode() + b'\n')
    except Exception as e:
        print(f"Error sending init to player {player_id}: {e}")
        return

    buffer = ""
    last_shoot = False

    while running:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line:
                    try:
                        inputs = json.loads(line)
                        with lock:
                            client_inputs[player_id] = inputs

                            # Handle Space input to spawn bullet
                            shoot_now = inputs.get('space', False)
                            if shoot_now and not last_shoot and player_id in game_state['players']:
                                player = game_state['players'][player_id]
                                bullet = Bullet(player.x, player.y, player.angle)
                                game_state['bullets'].append(bullet)
                            last_shoot = shoot_now
                    except json.JSONDecodeError:
                        pass
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"Error receiving from player {player_id}: {e}")
            break

    # Cleanup on disconnect
    with lock:
        if player_id in game_state['players']:
            del game_state['players'][player_id]
        if player_id in client_sockets:
            del client_sockets[player_id]
        if player_id in client_inputs:
            del client_inputs[player_id]

    try:
        client_socket.close()
    except:
        pass

    print(f"Player {player_id} disconnected")


def game_loop():
    """Game Loop running at 60 FPS: Update players/bullets, remove out-of-bound bullets."""
    while running:
        start_time = time.time()

        with lock:
            # Update all players based on inputs
            for player_id, player in game_state['players'].items():
                inputs = client_inputs.get(player_id, {})
                player.move(inputs)

                # Wrap around screen edges
                player.x = player.x % SCREEN_WIDTH
                player.y = player.y % SCREEN_HEIGHT

            # Update all bullets
            for bullet in game_state['bullets']:
                bullet.move()

            # Remove out-of-bounds bullets
            game_state['bullets'] = [
                b for b in game_state['bullets']
                if not b.is_out_of_bounds(SCREEN_WIDTH, SCREEN_HEIGHT)
            ]

            # Prepare broadcast game_state dict
            broadcast_state = {
                'type': 'state',
                'players': {
                    str(pid): p.get_state() for pid, p in game_state['players'].items()
                },
                'bullets': [
                    (b.x, b.y, b.angle) for b in game_state['bullets']
                ]
            }

            # Broadcast to all clients
            state_json = json.dumps(broadcast_state) + '\n'
            disconnected = []
            for player_id, sock in client_sockets.items():
                try:
                    sock.send(state_json.encode())
                except:
                    disconnected.append(player_id)

            for player_id in disconnected:
                if player_id in client_sockets:
                    del client_sockets[player_id]

        # Maintain 60 FPS
        elapsed = time.time() - start_time
        sleep_time = FRAME_TIME - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


def start_server():
    """Setup TCP Socket server on 0.0.0.0:21001."""
    global next_player_id, running

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(8)
    server_socket.settimeout(1.0)

    print("=" * 40)
    print("  MULTIPLAYER DOGFIGHT SERVER")
    print("=" * 40)
    print(f"Server started on {HOST}:{PORT}")
    print("Waiting for players...")
    print()

    # Start game loop in separate thread
    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()

    try:
        while running:
            try:
                client_socket, address = server_socket.accept()
                player_id = next_player_id
                next_player_id += 1

                # Create player with spawn position
                spawn_x = 100 + (player_id * 150) % (SCREEN_WIDTH - 200)
                spawn_y = 100 + (player_id * 100) % (SCREEN_HEIGHT - 200)
                color = COLORS[player_id % len(COLORS)]

                with lock:
                    game_state['players'][player_id] = Player(spawn_x, spawn_y, color)
                    client_sockets[player_id] = client_socket
                    client_inputs[player_id] = {}

                # Handle client in new thread
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, player_id),
                    daemon=True
                )
                client_thread.start()

                print(f"Player {player_id} ({color}) joined from {address}")

            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nShutting down server...")
        running = False
    finally:
        server_socket.close()
        print("Server closed.")


if _name_ == '_main_':
    start_server()