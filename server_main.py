import socket
import threading
import json
import time
import random
import os
from game_objects import Player, Bullet, MathBullet, NPC, Boss, check_collision, get_distance

# Server configuration
HOST = '0.0.0.0'
PORT = 9999
FPS = 60
FRAME_TIME = 1 / FPS
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Spawning configuration
MAX_NPCS = 5
NPC_SPAWN_INTERVAL = 5  # seconds

# Game state
game_state = {
    'players': {},  # {player_id: Player object}
    'bullets': [],  # [Bullet objects]
    'npcs': [],     # [NPC objects]
    'boss': None    # Boss object or None
}
client_sockets = {}  # {player_id: socket}
client_inputs = {}   # {player_id: {w, a, s, d, space}}
frame_events = []    # Events to send to clients this frame
lock = threading.Lock()
next_player_id = 0
next_npc_id = 0
running = True
last_npc_spawn = 0

# Boss / checkpoint progression
boss_level = 1          # Next boss is level 1 (threshold = 10*level)
checkpoint_score = 0    # Server-wide checkpoint restored on player death

# Bullet pattern configuration
PATTERN_FILE = "pattern.json"
DEFAULT_EXPRESSION = "50 * math.sin(x / 10)"
current_expression = DEFAULT_EXPRESSION

# Player colors
COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta']


def add_event(event_type, x, y, color='white'):
    """Add an event to be sent to clients."""
    frame_events.append({
        'type': event_type,
        'x': x,
        'y': y,
        'color': color
    })


def get_total_score():
    """Calculate total score of all players."""
    return sum(p.score for p in game_state['players'].values())


def find_nearest_player(x, y):
    """Find the nearest player to the given position."""
    nearest = None
    min_dist = float('inf')

    for player in game_state['players'].values():
        dist = get_distance(x, y, player.x, player.y)
        if dist < min_dist:
            min_dist = dist
            nearest = player

    return nearest


def load_pattern():
    """Load bullet pattern expression from pattern.json (written by web app)."""
    global current_expression
    try:
        if os.path.exists(PATTERN_FILE):
            with open(PATTERN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            expr = data.get('expression', DEFAULT_EXPRESSION)
            if expr != current_expression:
                current_expression = expr
                print(f"Loaded new bullet pattern: {data.get('name', '?')} -> {expr}")
    except Exception as e:
        print(f"Error loading pattern.json: {e}")


def spawn_npc():
    """Spawn a new NPC at a random edge of the screen."""
    global next_npc_id

    if len(game_state['npcs']) >= MAX_NPCS:
        return

    # Spawn at random edge
    edge = random.choice(['top', 'bottom', 'left', 'right'])
    if edge == 'top':
        x, y = random.randint(50, SCREEN_WIDTH - 50), 10
    elif edge == 'bottom':
        x, y = random.randint(50, SCREEN_WIDTH - 50), SCREEN_HEIGHT - 10
    elif edge == 'left':
        x, y = 10, random.randint(50, SCREEN_HEIGHT - 50)
    else:
        x, y = SCREEN_WIDTH - 10, random.randint(50, SCREEN_HEIGHT - 50)

    npc = NPC(x, y, next_npc_id)
    game_state['npcs'].append(npc)
    next_npc_id += 1
    print(f"NPC {npc.npc_id} spawned at ({x:.0f}, {y:.0f})")


def spawn_boss():
    """Spawn the boss at the center top of the screen.
    Uses boss_level to scale HP (500 * 2^(level-1)).
    """
    if game_state['boss'] is not None:
        return

    boss = Boss(SCREEN_WIDTH // 2, 50, 999, level=boss_level)
    game_state['boss'] = boss
    print("=" * 40)
    print(f"  BOSS LEVEL {boss_level} HAS SPAWNED!  (HP: {boss.max_hp})")
    print("=" * 40)


def handle_body_collisions():
    """Handle Player vs Enemy body collisions (crash damage)."""
    import math

    for player_id, player in game_state['players'].items():
        # === Player vs NPC collision ===
        for npc in game_state['npcs'][:]:
            if check_collision(player, npc):
                # Player takes 30 crash damage
                is_player_dead = player.take_damage(30)
                add_event('hit', player.x, player.y, player.color)
                print(f"Player {player_id} crashed into NPC! -30 HP")

                # Kill the NPC immediately
                add_event('explode', npc.x, npc.y, 'npc')
                game_state['npcs'].remove(npc)
                print(f"NPC destroyed by collision!")

                # Check if player died from crash
                if is_player_dead:
                    add_event('explode', player.x, player.y, player.color)
                    spawn_x = random.randint(100, SCREEN_WIDTH - 100)
                    spawn_y = random.randint(100, SCREEN_HEIGHT - 100)
                    player.respawn(spawn_x, spawn_y)
                    print(f"Player {player_id} died from crash and respawned!")

        # === Player vs Boss collision ===
        if game_state['boss'] is not None:
            boss = game_state['boss']
            if check_collision(player, boss):
                # Player takes 50 massive crash damage
                is_player_dead = player.take_damage(50)
                add_event('hit', player.x, player.y, player.color)
                print(f"Player {player_id} crashed into BOSS! -50 HP")

                # Knockback player away from boss to prevent getting stuck
                dx = player.x - boss.x
                dy = player.y - boss.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    # Push player backwards
                    knockback_strength = 50
                    player.x += (dx / dist) * knockback_strength
                    player.y += (dy / dist) * knockback_strength

                    # Keep player on screen
                    player.x = max(20, min(SCREEN_WIDTH - 20, player.x))
                    player.y = max(20, min(SCREEN_HEIGHT - 20, player.y))

                # Check if player died from crash
                if is_player_dead:
                    add_event('explode', player.x, player.y, player.color)
                    spawn_x = random.randint(100, SCREEN_WIDTH - 100)
                    spawn_y = random.randint(100, SCREEN_HEIGHT - 100)
                    player.respawn(spawn_x, spawn_y)
                    print(f"Player {player_id} died from Boss crash and respawned!")


def handle_collisions():
    """Handle all bullet collision logic with explosion events."""
    global boss_level, checkpoint_score
    bullets_to_remove = []

    for bullet in game_state['bullets']:
        # Bullet vs Player collision
        for player_id, player in game_state['players'].items():
            # Don't hit yourself (players can't hit themselves)
            if bullet.owner_id == player_id:
                continue
            if check_collision(bullet, player):
                is_dead = player.take_damage(bullet.damage)
                bullets_to_remove.append(bullet)

                # Add hit event for screen shake
                add_event('hit', player.x, player.y, player.color)
                print(f"Player {player_id} hit! HP: {player.hp}")

                if is_dead:
                    # Add explosion event
                    add_event('explode', player.x, player.y, player.color)
                    # Respawn player and reset score
                    spawn_x = random.randint(100, SCREEN_WIDTH - 100)
                    spawn_y = random.randint(100, SCREEN_HEIGHT - 100)
                    player.respawn(spawn_x, spawn_y)
                    print(f"Player {player_id} died and respawned!")
                break

        # Bullet vs NPC collision
        for npc in game_state['npcs'][:]:
            if bullet in bullets_to_remove:
                break
            if check_collision(bullet, npc):
                is_dead = npc.take_damage(bullet.damage)
                bullets_to_remove.append(bullet)

                if is_dead:
                    # Add explosion event for NPC death
                    add_event('explode', npc.x, npc.y, 'npc')
                    game_state['npcs'].remove(npc)
                    # Give score to shooter if it's a player
                    if bullet.owner_id in game_state['players']:
                        game_state['players'][bullet.owner_id].score += 1
                        print(f"Player {bullet.owner_id} killed NPC! Score: {game_state['players'][bullet.owner_id].score}")
                break

        # Bullet vs Boss collision
        if game_state['boss'] is not None and bullet not in bullets_to_remove:
            if check_collision(bullet, game_state['boss']):
                is_dead = game_state['boss'].take_damage(bullet.damage)
                bullets_to_remove.append(bullet)

                if is_dead:
                    # Add big explosion event for Boss death
                    add_event('explode_big', game_state['boss'].x, game_state['boss'].y, 'boss')
                    # Give score to shooter
                    if bullet.owner_id in game_state['players']:
                        game_state['players'][bullet.owner_id].score += 5
                        print(f"Player {bullet.owner_id} killed the BOSS! +5 Score!")
                    game_state['boss'] = None

                    # Advance checkpoint to the threshold we just cleared
                    checkpoint_score = 10 * boss_level
                    for p in game_state['players'].values():
                        p.checkpoint_score = checkpoint_score
                    print(f"BOSS LEVEL {boss_level} DEFEATED! Checkpoint updated to {checkpoint_score}.")
                    boss_level += 1

    # Remove hit bullets
    for bullet in bullets_to_remove:
        if bullet in game_state['bullets']:
            game_state['bullets'].remove(bullet)


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

                            # Handle Space input to spawn MathBullet
                            shoot_now = inputs.get('space', False)
                            if shoot_now and not last_shoot and player_id in game_state['players']:
                                player = game_state['players'][player_id]
                                load_pattern()
                                bullet = MathBullet(
                                    player.x, player.y, player.angle,
                                    owner_id=player_id,
                                    expression=current_expression
                                )
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
    """Game Loop running at 60 FPS with spawning and collision logic."""
    global last_npc_spawn, frame_events

    while running:
        start_time = time.time()

        with lock:
            # Clear events from previous frame
            frame_events = []

            # === SPAWNING LOGIC ===
            if len(game_state['players']) > 0:
                total = get_total_score()
                boss_threshold = 10 * boss_level  # 10, 20, 30, ...

                if total >= boss_threshold and game_state['boss'] is None:
                    spawn_boss()

                # Solo Boss: only spawn NPCs when boss is NOT active
                if game_state['boss'] is None:
                    if time.time() - last_npc_spawn > NPC_SPAWN_INTERVAL:
                        spawn_npc()
                        last_npc_spawn = time.time()

            # === UPDATE PLAYERS ===
            for player_id, player in game_state['players'].items():
                inputs = client_inputs.get(player_id, {})
                player.move(inputs)

                # Wrap around screen edges
                player.x = player.x % SCREEN_WIDTH
                player.y = player.y % SCREEN_HEIGHT

            # === UPDATE NPCs (move towards nearest player) ===
            for npc in game_state['npcs']:
                nearest = find_nearest_player(npc.x, npc.y)
                if nearest:
                    npc.move_towards_target(nearest.x, nearest.y)

                # Keep NPCs on screen
                npc.x = max(10, min(SCREEN_WIDTH - 10, npc.x))
                npc.y = max(10, min(SCREEN_HEIGHT - 10, npc.y))

            # === UPDATE BOSS ===
            if game_state['boss'] is not None:
                boss = game_state['boss']
                nearest = find_nearest_player(boss.x, boss.y)
                if nearest:
                    boss.move_towards_target(nearest.x, nearest.y)

                # Keep Boss on screen
                boss.x = max(50, min(SCREEN_WIDTH - 50, boss.x))
                boss.y = max(50, min(SCREEN_HEIGHT - 50, boss.y))

                # === BOSS ATTACK: Fire 8 bullets every 2 seconds ===
                if boss.update_attack():
                    bullet_data_list = boss.get_attack_bullets()
                    for bdata in bullet_data_list:
                        bullet = Bullet(
                            bdata['x'], bdata['y'], bdata['angle'],
                            owner_id=bdata['owner_id'],
                            speed=bdata['speed'],
                            damage=bdata['damage']
                        )
                        game_state['bullets'].append(bullet)
                    # Add boss attack event
                    add_event('boss_attack', boss.x, boss.y, 'boss')
                    print("Boss fired!")

            # === UPDATE BULLETS ===
            for bullet in game_state['bullets']:
                bullet.move()

            # Remove out-of-bounds bullets
            game_state['bullets'] = [
                b for b in game_state['bullets']
                if not b.is_out_of_bounds(SCREEN_WIDTH, SCREEN_HEIGHT)
            ]

            # === COLLISION LOGIC ===
            handle_collisions()        # Bullet collisions
            handle_body_collisions()   # Player vs Enemy body collisions

            # === PREPARE BROADCAST STATE ===
            broadcast_state = {
                'type': 'state',
                'players': {
                    str(pid): p.get_state() for pid, p in game_state['players'].items()
                },
                'bullets': [
                    (b.x, b.y, b.angle, b.owner_id) for b in game_state['bullets']
                ],
                'npcs': [
                    npc.get_state() for npc in game_state['npcs']
                ],
                'boss': game_state['boss'].get_state() if game_state['boss'] else None,
                'events': frame_events  # Send events to clients
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
    """Setup TCP Socket server."""
    global next_player_id, running, last_npc_spawn

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(8)
    server_socket.settimeout(1.0)

    last_npc_spawn = time.time()

    print("=" * 40)
    print("  MULTIPLAYER DOGFIGHT SERVER")
    print("  With NPCs, Boss Attacks & Effects!")
    print("=" * 40)
    print(f"Server started on {HOST}:{PORT}")
    print(f"NPC spawn interval: {NPC_SPAWN_INTERVAL}s (max {MAX_NPCS})")
    print(f"Boss spawns at total score thresholds: 10, 20, 30, ...")
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
                    player = Player(spawn_x, spawn_y, color)
                    player.checkpoint_score = checkpoint_score
                    player.score = checkpoint_score
                    game_state['players'][player_id] = player
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


if __name__ == '__main__':
    start_server()
