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
HP_GREEN = (50, 255, 50)
HP_RED = (255, 50, 50)
HP_BG = (100, 100, 100)


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

    def draw_background(self):
        """Clear screen and draw starfield background."""
        self.screen.fill(DARK_BLUE)

        # Draw stars
        for star_x, star_y, brightness in self.stars:
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (star_x, star_y), 1)

    def draw_health_bar(self, x, y, hp, max_hp, width=40, height=6):
        """Draw health bar above entity (Green line for HP, Red line for background)."""
        bar_x = x - width // 2
        bar_y = y - 25

        # Background (red)
        pygame.draw.rect(self.screen, HP_RED, (bar_x, bar_y, width, height))

        # HP (green)
        hp_width = int((hp / max_hp) * width) if max_hp > 0 else 0
        if hp_width > 0:
            pygame.draw.rect(self.screen, HP_GREEN, (bar_x, bar_y, hp_width, height))

        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, width, height), 1)

    def draw_player(self, x, y, angle, color, size=20):
        """
        Draw Players using pygame.draw.polygon.
        Draw a Triangle rotated by 'angle' with nose pointing forward.
        """
        angle_rad = math.radians(angle)

        # Calculate 3 points of triangle rotated by angle
        # Nose (front) - points in direction of angle
        nose_x = x + math.cos(angle_rad) * size
        nose_y = y + math.sin(angle_rad) * size

        # Left wing (140 degrees offset)
        left_angle = angle_rad + math.radians(140)
        left_x = x + math.cos(left_angle) * (size * 0.8)
        left_y = y + math.sin(left_angle) * (size * 0.8)

        # Right wing (-140 degrees offset)
        right_angle = angle_rad - math.radians(140)
        right_x = x + math.cos(right_angle) * (size * 0.8)
        right_y = y + math.sin(right_angle) * (size * 0.8)

        # Get RGB color
        rgb_color = COLORS.get(color, WHITE)

        # Draw the triangle polygon
        points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(self.screen, rgb_color, points)
        pygame.draw.polygon(self.screen, WHITE, points, 2)  # Outline

    def draw_npc(self, x, y, angle, hp, max_hp):
        """Draw NPC (Blue Color) with health bar."""
        # Draw NPC as blue triangle
        self.draw_player(x, y, angle, 'npc', size=18)

        # Draw health bar
        self.draw_health_bar(x, y, hp, max_hp, width=30, height=4)

    def draw_boss(self, x, y, angle, hp, max_hp):
        """Draw Boss (Big Purple Color) with large health bar."""
        # Draw Boss as larger purple triangle
        self.draw_player(x, y, angle, 'boss', size=40)

        # Draw large health bar
        self.draw_health_bar(x, y - 20, hp, max_hp, width=80, height=8)

        # Draw "BOSS" label
        label = self.font.render("BOSS", True, (255, 100, 255))
        self.screen.blit(label, (x - 20, y - 55))

    def draw_bullet(self, x, y):
        """Draw Bullets as small circles."""
        pygame.draw.circle(self.screen, BULLET_COLOR, (int(x), int(y)), 4)
        pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), 2)

    def draw(self, game_state, my_id):
        """
        Main draw method: Clear screen, draw background, players, NPCs, Boss, and bullets.

        Args:
            game_state: Dict with 'players', 'bullets', 'npcs', 'boss' data
            my_id: This client's player ID
        """
        # Clear screen and draw background
        self.draw_background()

        # Draw all NPCs (Blue Color)
        npcs = game_state.get('npcs', [])
        for npc_data in npcs:
            x, y, angle, color, hp, max_hp = npc_data
            self.draw_npc(x, y, angle, hp, max_hp)

        # Draw Boss (Big Purple Color) if present
        boss_data = game_state.get('boss')
        if boss_data:
            x, y, angle, color, hp, max_hp = boss_data
            self.draw_boss(x, y, angle, hp, max_hp)

        # Draw all players with health bars
        players = game_state.get('players', {})
        my_score = 0
        my_hp = 100
        my_max_hp = 100

        for player_id, player_data in players.items():
            x, y, angle, color, hp, max_hp, score = player_data
            self.draw_player(x, y, angle, color)

            # Draw health bar
            self.draw_health_bar(x, y, hp, max_hp)

            # Draw player label
            label = f"P{player_id}"
            if str(player_id) == str(my_id):
                label += " (YOU)"
                my_score = score
                my_hp = hp
                my_max_hp = max_hp
            label_surface = self.font.render(label, True, WHITE)
            self.screen.blit(label_surface, (x - 20, y - 40))

        # Draw all bullets
        bullets = game_state.get('bullets', [])
        for bullet_data in bullets:
            x, y, angle = bullet_data
            self.draw_bullet(x, y)

        # Draw HUD with score
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
            # Player ID
            status = self.font.render(f"Player: {my_id}", True, WHITE)
            self.screen.blit(status, (10, 10))

            # Score display (prominent)
            score_text = self.score_font.render(f"SCORE: {score}", True, (255, 255, 100))
            self.screen.blit(score_text, (10, 35))

            # HP display
            hp_text = self.font.render(f"HP: {hp}/{max_hp}", True, HP_GREEN if hp > 30 else HP_RED)
            self.screen.blit(hp_text, (10, 65))

            # Enemy count
            enemy_text = self.font.render(f"NPCs: {npc_count}", True, COLORS['npc'])
            self.screen.blit(enemy_text, (10, 90))

            # Boss status
            if boss_alive:
                boss_text = self.font.render("BOSS ACTIVE!", True, COLORS['boss'])
                self.screen.blit(boss_text, (SCREEN_WIDTH - 120, 10))
        else:
            status = self.font.render("Connecting...", True, WHITE)
            self.screen.blit(status, (10, 10))

        # Player count (top right)
        count = self.font.render(f"Players: {player_count}", True, WHITE)
        self.screen.blit(count, (SCREEN_WIDTH - 100, 35))

        # Controls help
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
