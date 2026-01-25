import pygame
import math
import random

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
COLORS = {
    'red': (255, 50, 50),
    'blue': (50, 100, 255),
    'green': (50, 255, 50),
    'yellow': (255, 255, 50),
    'purple': (180, 50, 255),
    'orange': (255, 165, 0),
    'cyan': (0, 255, 255),
    'magenta': (255, 50, 255),
    'white': (255, 255, 255),
    'npc': (50, 150, 255),      # Blue color for NPCs
    'boss': (200, 50, 255),     # Big Purple for Boss
}
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (10, 10, 40)
BULLET_COLOR = (255, 255, 100)
BOSS_BULLET_COLOR = (255, 100, 255)  # Purple bullets for boss
HP_GREEN = (50, 255, 50)
HP_RED = (255, 50, 50)
HP_BG = (100, 100, 100)


class Particle:
    """Particle class for explosion effects."""

    def __init__(self, x, y, dx, dy, lifetime, color):
        self.x = x
        self.y = y
        self.dx = dx  # Velocity X
        self.dy = dy  # Velocity Y
        self.lifetime = lifetime  # Frames remaining
        self.max_lifetime = lifetime
        self.color = color

    def update(self):
        """Update particle position and lifetime."""
        self.x += self.dx
        self.y += self.dy
        self.dx *= 0.95  # Friction
        self.dy *= 0.95
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        """Draw particle with fading effect."""
        alpha = self.lifetime / self.max_lifetime
        size = max(1, int(3 * alpha))
        color = tuple(int(c * alpha) for c in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)


class GameRenderer:
    def __init__(self):
        """Init Pygame with 800x600 screen."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Multiplayer Dogfight - Top Gun Style")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.score_font = pygame.font.Font(None, 32)

        # Generate static star positions for background
        random.seed(42)
        self.stars = [
            (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(100, 255))
            for _ in range(100)
        ]

        # Particle system for explosions
        self.particles = []

        # Screen shake
        self.shake_intensity = 0
        self.shake_duration = 0

    def create_explosion(self, x, y, color, count=15):
        """Spawn particles for explosion effect."""
        rgb_color = COLORS.get(color, WHITE)
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = random.randint(20, 40)
            # Vary color slightly
            varied_color = tuple(min(255, c + random.randint(-30, 30)) for c in rgb_color)
            self.particles.append(Particle(x, y, dx, dy, lifetime, varied_color))

    def create_big_explosion(self, x, y, color):
        """Create a larger explosion for boss death."""
        self.create_explosion(x, y, color, count=40)
        # Add extra ring of particles
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            speed = random.uniform(5, 10)
            dx = math.cos(rad) * speed
            dy = math.sin(rad) * speed
            self.particles.append(Particle(x, y, dx, dy, 50, COLORS.get(color, WHITE)))

    def trigger_screen_shake(self, intensity=5, duration=10):
        """Trigger screen shake effect."""
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)

    def get_shake_offset(self):
        # แปลงเป็นจำนวนเต็มก่อน (int)
        intensity = int(self.shake_intensity) 
        
        if intensity > 0:
            # ใช้ตัวแปร intensity ที่เป็นจำนวนเต็มแล้วแทน
            offset_x = random.randint(-intensity, intensity)
            offset_y = random.randint(-intensity, intensity)
            
            self.shake_intensity *= 0.9  # ลดแรงสั่น
            if self.shake_intensity < 0.5:
                self.shake_intensity = 0
            return offset_x, offset_y
        return 0, 0

    def process_events(self, events, my_x, my_y):
        """Process server events and trigger visual effects."""
        for event in events:
            event_type = event.get('type')
            x = event.get('x', 0)
            y = event.get('y', 0)
            color = event.get('color', 'white')

            if event_type == 'explode':
                self.create_explosion(x, y, color)
                # Screen shake if nearby
                dist = math.sqrt((x - my_x) ** 2 + (y - my_y) ** 2)
                if dist < 200:
                    self.trigger_screen_shake(intensity=8, duration=15)

            elif event_type == 'explode_big':
                self.create_big_explosion(x, y, color)
                self.trigger_screen_shake(intensity=15, duration=25)

            elif event_type == 'hit':
                # Small hit effect
                self.create_explosion(x, y, color, count=5)
                # Shake if it's near the player
                dist = math.sqrt((x - my_x) ** 2 + (y - my_y) ** 2)
                if dist < 50:
                    self.trigger_screen_shake(intensity=5, duration=8)

            elif event_type == 'boss_attack':
                # Visual feedback for boss attack
                self.create_explosion(x, y, 'boss', count=8)

    def update_particles(self):
        """Update and remove dead particles."""
        self.particles = [p for p in self.particles if p.update()]

    def draw_particles(self, offset_x, offset_y):
        """Draw all particles with screen offset."""
        for particle in self.particles:
            # Apply screen shake offset
            draw_x = particle.x + offset_x
            draw_y = particle.y + offset_y
            alpha = particle.lifetime / particle.max_lifetime
            size = max(1, int(3 * alpha))
            color = tuple(max(0, min(255, int(c * alpha))) for c in particle.color)
            pygame.draw.circle(self.screen, color, (int(draw_x), int(draw_y)), size)

    def draw_background(self):
        """Clear screen and draw starfield background."""
        self.screen.fill(DARK_BLUE)

        # Draw stars
        for star_x, star_y, brightness in self.stars:
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (star_x, star_y), 1)

    def draw_health_bar(self, x, y, hp, max_hp, width=30, height=4, offset_x=0, offset_y=0):
        """Draw health bar above entity (Green line for HP, Red line for background)."""
        bar_x = x - width // 2 + offset_x
        bar_y = y - 18 + offset_y  # Closer to smaller entity

        # Background (red)
        pygame.draw.rect(self.screen, HP_RED, (bar_x, bar_y, width, height))

        # HP (green)
        hp_width = int((hp / max_hp) * width) if max_hp > 0 else 0
        if hp_width > 0:
            pygame.draw.rect(self.screen, HP_GREEN, (bar_x, bar_y, hp_width, height))

        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, width, height), 1)

    def draw_player(self, x, y, angle, color, size=12, offset_x=0, offset_y=0):
        """Draw Players using pygame.draw.polygon with screen shake offset (smaller size)."""
        x += offset_x
        y += offset_y
        angle_rad = math.radians(angle)

        # Calculate 3 points of triangle rotated by angle
        nose_x = x + math.cos(angle_rad) * size
        nose_y = y + math.sin(angle_rad) * size

        left_angle = angle_rad + math.radians(140)
        left_x = x + math.cos(left_angle) * (size * 0.8)
        left_y = y + math.sin(left_angle) * (size * 0.8)

        right_angle = angle_rad - math.radians(140)
        right_x = x + math.cos(right_angle) * (size * 0.8)
        right_y = y + math.sin(right_angle) * (size * 0.8)

        rgb_color = COLORS.get(color, WHITE)
        points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(self.screen, rgb_color, points)
        pygame.draw.polygon(self.screen, WHITE, points, 2)

    def draw_npc(self, x, y, angle, hp, max_hp, offset_x=0, offset_y=0):
        """Draw NPC (Blue Color) with health bar (smaller)."""
        self.draw_player(x, y, angle, 'npc', size=10, offset_x=offset_x, offset_y=offset_y)
        self.draw_health_bar(x, y, hp, max_hp, width=20, height=3, offset_x=offset_x, offset_y=offset_y)

    def draw_boss(self, x, y, angle, hp, max_hp, offset_x=0, offset_y=0):
        """Draw Boss (Purple Color) with health bar (smaller)."""
        self.draw_player(x, y, angle, 'boss', size=25, offset_x=offset_x, offset_y=offset_y)
        self.draw_health_bar(x, y - 12, hp, max_hp, width=50, height=6, offset_x=offset_x, offset_y=offset_y)

        label = self.font.render("BOSS", True, (255, 100, 255))
        self.screen.blit(label, (x - 18 + offset_x, y - 38 + offset_y))

    def draw_bullet(self, x, y, owner_id='player', offset_x=0, offset_y=0):
        """Draw Bullets with different colors for boss bullets."""
        draw_x = int(x + offset_x)
        draw_y = int(y + offset_y)

        if owner_id == 'boss':
            # Boss bullets are purple and slightly larger
            pygame.draw.circle(self.screen, BOSS_BULLET_COLOR, (draw_x, draw_y), 5)
            pygame.draw.circle(self.screen, WHITE, (draw_x, draw_y), 3)
        else:
            pygame.draw.circle(self.screen, BULLET_COLOR, (draw_x, draw_y), 4)
            pygame.draw.circle(self.screen, WHITE, (draw_x, draw_y), 2)

    def draw(self, game_state, my_id):
        """Main draw method with particles and screen shake."""
        # Update particles
        self.update_particles()

        # Get screen shake offset
        offset_x, offset_y = self.get_shake_offset()

        # Get player position for distance calculations
        my_x, my_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        players = game_state.get('players', {})
        if my_id is not None and str(my_id) in players:
            player_data = players[str(my_id)]
            my_x, my_y = player_data[0], player_data[1]

        # Process server events
        events = game_state.get('events', [])
        self.process_events(events, my_x, my_y)

        # Clear screen and draw background
        self.draw_background()

        # Draw all NPCs (Blue Color)
        npcs = game_state.get('npcs', [])
        for npc_data in npcs:
            x, y, angle, color, hp, max_hp = npc_data
            self.draw_npc(x, y, angle, hp, max_hp, offset_x, offset_y)

        # Draw Boss if present
        boss_data = game_state.get('boss')
        if boss_data:
            x, y, angle, color, hp, max_hp = boss_data
            self.draw_boss(x, y, angle, hp, max_hp, offset_x, offset_y)

        # Draw all players with health bars
        my_score = 0
        my_hp = 100
        my_max_hp = 100

        for player_id, player_data in players.items():
            x, y, angle, color, hp, max_hp, score = player_data
            self.draw_player(x, y, angle, color, offset_x=offset_x, offset_y=offset_y)
            self.draw_health_bar(x, y, hp, max_hp, offset_x=offset_x, offset_y=offset_y)

            label = f"P{player_id}"
            if str(player_id) == str(my_id):
                label += " (YOU)"
                my_score = score
                my_hp = hp
                my_max_hp = max_hp
            label_surface = self.font.render(label, True, WHITE)
            self.screen.blit(label_surface, (x - 15 + offset_x, y - 30 + offset_y))  # Adjusted for smaller size

        # Draw all bullets (with owner info for coloring)
        bullets = game_state.get('bullets', [])
        for bullet_data in bullets:
            if len(bullet_data) >= 4:
                x, y, angle, owner_id = bullet_data
            else:
                x, y, angle = bullet_data
                owner_id = 'player'
            self.draw_bullet(x, y, owner_id, offset_x, offset_y)

        # Draw particles on top
        self.draw_particles(offset_x, offset_y)

        # Draw HUD (no shake for HUD)
        self.draw_hud(my_id, len(players), my_score, my_hp, my_max_hp, len(npcs), boss_data is not None)

        # Update display
        pygame.display.flip()
        self.clock.tick(60)

    def draw_hud(self, my_id, player_count, score, hp, max_hp, npc_count, boss_alive):
        """Draw heads-up display with game info and score."""
        # Title
        title = self.title_font.render("DOGFIGHT", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 60, 10))

        # Player info
        if my_id is not None:
            status = self.font.render(f"Player: {my_id}", True, WHITE)
            self.screen.blit(status, (10, 10))

            score_text = self.score_font.render(f"SCORE: {score}", True, (255, 255, 100))
            self.screen.blit(score_text, (10, 35))

            hp_text = self.font.render(f"HP: {hp}/{max_hp}", True, HP_GREEN if hp > 30 else HP_RED)
            self.screen.blit(hp_text, (10, 65))

            enemy_text = self.font.render(f"NPCs: {npc_count}", True, COLORS['npc'])
            self.screen.blit(enemy_text, (10, 90))

            if boss_alive:
                boss_text = self.font.render("BOSS ACTIVE!", True, COLORS['boss'])
                self.screen.blit(boss_text, (SCREEN_WIDTH - 120, 10))
        else:
            status = self.font.render("Connecting...", True, WHITE)
            self.screen.blit(status, (10, 10))

        count = self.font.render(f"Players: {player_count}", True, WHITE)
        self.screen.blit(count, (SCREEN_WIDTH - 100, 35))

        controls = "W/S: Speed | A/D: Turn | SPACE: Shoot | Kill NPCs to score!"
        help_text = self.font.render(controls, True, (150, 150, 150))
        self.screen.blit(help_text, (SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT - 25))

    def handle_events(self):
        """Process pygame events. Returns False if quit requested."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def get_inputs(self):
        """Get current keyboard state for WASD + Space."""
        keys = pygame.key.get_pressed()
        return {
            'w': keys[pygame.K_w],
            's': keys[pygame.K_s],
            'a': keys[pygame.K_a],
            'd': keys[pygame.K_d],
            'space': keys[pygame.K_SPACE]
        }

    def quit(self):
        """Clean up pygame."""
        pygame.quit()
