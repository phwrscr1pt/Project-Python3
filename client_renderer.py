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
}
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (10, 10, 40)
BULLET_COLOR = (255, 255, 100)


class GameRenderer:
    def __init__(self):
        """Init Pygame with 800x600 screen."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Multiplayer Dogfight - Top Gun Style")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

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

    def draw_player(self, x, y, angle, color):
        """
        Draw Players using pygame.draw.polygon.
        Draw a Triangle rotated by 'angle' with nose pointing forward.
        """
        size = 20
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

    def draw_bullet(self, x, y):
        """Draw Bullets as small circles."""
        pygame.draw.circle(self.screen, BULLET_COLOR, (int(x), int(y)), 4)
        pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), 2)

    def draw(self, game_state, my_id):
        """
        Main draw method: Clear screen, draw background, players, and bullets.

        Args:
            game_state: Dict with 'players' and 'bullets' data
            my_id: This client's player ID
        """
        # Clear screen and draw background
        self.draw_background()

        # Draw all players
        players = game_state.get('players', {})
        for player_id, player_data in players.items():
            x, y, angle, color = player_data
            self.draw_player(x, y, angle, color)

            # Draw player label
            label = f"P{player_id}"
            if str(player_id) == str(my_id):
                label += " (YOU)"
            label_surface = self.font.render(label, True, WHITE)
            self.screen.blit(label_surface, (x - 20, y - 35))

        # Draw all bullets
        bullets = game_state.get('bullets', [])
        for bullet_data in bullets:
            x, y, angle = bullet_data
            self.draw_bullet(x, y)

        # Draw HUD
        self.draw_hud(my_id, len(players))

        # Update display
        pygame.display.flip()
        self.clock.tick(60)

    def draw_hud(self, my_id, player_count):
        """Draw heads-up display with game info."""
        # Title
        title = self.title_font.render("DOGFIGHT", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 60, 10))

        # Player info
        if my_id is not None:
            status = self.font.render(f"Player: {my_id}", True, WHITE)
            self.screen.blit(status, (10, 10))

            count = self.font.render(f"Players: {player_count}", True, WHITE)
            self.screen.blit(count, (10, 35))
        else:
            status = self.font.render("Connecting...", True, WHITE)
            self.screen.blit(status, (10, 10))

        # Controls help
        controls = "W/S: Speed | A/D: Turn | SPACE: Shoot"
        help_text = self.font.render(controls, True, (150, 150, 150))
        self.screen.blit(help_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 25))

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
