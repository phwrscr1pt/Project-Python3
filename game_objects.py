import math
import random


class Player:
    HITBOX_RADIUS = 10  # Smaller hitbox

    def __init__(self, x, y, color, angle=0, speed=0):
        self.x = x
        self.y = y
        self.color = color
        self.angle = angle  # 0-360 degrees
        self.speed = speed  # 0-8 max
        self.hp = 100
        self.max_hp = 100
        self.score = 0
        self.checkpoint_score = 0  # Restored on death instead of 0

    def move(self, inputs):
        # Rotation
        if inputs.get('a'):
            self.angle = (self.angle - 5) % 360
        if inputs.get('d'):
            self.angle = (self.angle + 5) % 360

        # Speed control
        if inputs.get('w'):
            self.speed = min(self.speed + 0.3, 8)
        if inputs.get('s'):
            self.speed = max(self.speed - 0.3, 0)

        # Apply friction when not accelerating
        if not inputs.get('w') and self.speed > 0:
            self.speed = max(self.speed - 0.05, 0)

        # Calculate new position using math.cos/sin
        angle_rad = math.radians(self.angle)
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0

    def respawn(self, x, y):
        self.x = x
        self.y = y
        self.hp = self.max_hp
        self.speed = 0
        self.score = self.checkpoint_score

    def get_state(self):
        return (self.x, self.y, self.angle, self.color, self.hp, self.max_hp, self.score)


class Bullet:
    HITBOX_RADIUS = 5

    def __init__(self, x, y, angle, owner_id, speed=12, damage=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.owner_id = owner_id  # So players don't shoot themselves
        self.damage = damage

    def move(self):
        angle_rad = math.radians(self.angle)
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed

    def is_out_of_bounds(self, width, height):
        return self.x < 0 or self.x > width or self.y < 0 or self.y > height


class MathBullet:
    """Bullet that follows a math expression path (AI-generated pattern).
    The waveform offset is applied perpendicular to the direction of travel,
    so it works correctly at any firing angle."""
    HITBOX_RADIUS = 5

    def __init__(self, x, y, angle, owner_id, expression, speed=12, damage=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.owner_id = owner_id
        self.damage = damage
        self.expression = expression
        self.t = 0  # Time variable for expression evaluation

    def move(self):
        # Increment time
        self.t += 1

        angle_rad = math.radians(self.angle)
        perp_rad = angle_rad + math.pi / 2  # 90 degrees perpendicular

        # Move forward along the firing angle
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed

        # Calculate waveform offset and apply perpendicular to travel direction
        try:
            local_y = eval(self.expression, {"__builtins__": {}, "math": math, "x": self.t})
            self.x += local_y * math.cos(perp_rad)
            self.y += local_y * math.sin(perp_rad)
        except Exception:
            pass  # Fallback: straight line (no offset)

    def is_out_of_bounds(self, width, height):
        return self.x < 0 or self.x > width or self.y < 0 or self.y > height

    def get_state(self):
        return (self.x, self.y, self.angle, self.owner_id)


class NPC:
    """NPC class that moves automatically towards the nearest player."""
    HITBOX_RADIUS = 10  # Smaller hitbox

    def __init__(self, x, y, npc_id):
        self.x = x
        self.y = y
        self.npc_id = npc_id
        self.angle = random.uniform(0, 360)  # Random starting angle
        self.speed = random.uniform(2.0, 4.0)  # Randomize speed so NPCs don't stack
        self.turn_speed = 3  # Degrees per frame for smooth turning
        self.hp = 30
        self.max_hp = 30
        self.color = 'npc'  # Blue color identifier

    def move_towards_target(self, target_x, target_y):
        """Move automatically towards the target with smooth turning."""
        # Calculate target angle to player using atan2
        dx = target_x - self.x
        dy = target_y - self.y
        target_angle = math.degrees(math.atan2(dy, dx))

        # Calculate difference between current angle and target angle
        angle_diff = target_angle - self.angle

        # Normalize the difference to be between -180 and 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        # Gradually turn towards target angle by turn_speed
        if angle_diff > 0:
            self.angle += min(self.turn_speed, angle_diff)
        elif angle_diff < 0:
            self.angle += max(-self.turn_speed, angle_diff)

        # Keep angle in 0-360 range
        self.angle = self.angle % 360

        # Move forward in current facing direction
        angle_rad = math.radians(self.angle)
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0

    def get_state(self):
        return (self.x, self.y, self.angle, self.color, self.hp, self.max_hp)


class Boss(NPC):
    """Boss class - larger, slower, more HP than NPC.

    HP scales by level: 500 * 2^(level-1)  ->  500, 1000, 2000, ...
    Moves very slowly (creeping) towards the nearest player.
    Low fire rate but high damage.
    """
    HITBOX_RADIUS = 25  # Smaller but still larger than players
    ATTACK_INTERVAL = 150  # Frames (~2.5 seconds at 60 FPS) - low fire rate

    def __init__(self, x, y, boss_id, level=1):
        super().__init__(x, y, boss_id)
        self.level = level
        base_hp = 500 * (2 ** (level - 1))  # 500 -> 1000 -> 2000 ...
        self.hp = base_hp
        self.max_hp = base_hp
        self.speed = 0.6  # Very slow creeping speed
        self.turn_speed = 0.8  # Slow turn - feels heavy and menacing
        self.color = 'boss'
        self.shoot_cooldown = 0

    def update_attack(self):
        """Update attack cooldown. Returns True if ready to fire."""
        self.shoot_cooldown += 1
        if self.shoot_cooldown >= self.ATTACK_INTERVAL:
            self.shoot_cooldown = 0
            return True
        return False

    def get_attack_bullets(self):
        """Fire 8 bullets in all directions (turret pattern) with high damage."""
        bullets = []
        for angle in range(0, 360, 45):  # 0, 45, 90, 135, 180, 225, 270, 315
            bullets.append({
                'x': self.x,
                'y': self.y,
                'angle': angle,
                'owner_id': 'boss',
                'speed': 5,
                'damage': 25  # High damage per hit
            })
        return bullets
    # Boss inherits smooth turning from NPC.move_towards_target()


def check_collision(entity1, entity2):
    """
    Returns True if hitboxes of two entities overlap.
    Uses circle-based collision detection.
    """
    dx = entity1.x - entity2.x
    dy = entity1.y - entity2.y
    distance = math.sqrt(dx * dx + dy * dy)

    # Get hitbox radii (default to 15 if not defined)
    radius1 = getattr(entity1, 'HITBOX_RADIUS', 15)
    radius2 = getattr(entity2, 'HITBOX_RADIUS', 15)

    return distance < (radius1 + radius2)


def get_distance(x1, y1, x2, y2):
    """Calculate distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
