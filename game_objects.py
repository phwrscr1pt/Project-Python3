import math
import random


class Player:
    HITBOX_RADIUS = 15

    def __init__(self, x, y, color, angle=0, speed=0):
        self.x = x
        self.y = y
        self.color = color
        self.angle = angle  # 0-360 degrees
        self.speed = speed  # 0-8 max
        self.hp = 100
        self.max_hp = 100
        self.score = 0

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
        self.score = 0

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


class NPC:
    """NPC class that moves automatically towards the nearest player."""
    HITBOX_RADIUS = 15

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
    """Boss class - larger, slower, more HP than NPC."""
    HITBOX_RADIUS = 40  # Larger size

    def __init__(self, x, y, boss_id):
        super().__init__(x, y, boss_id)
        self.hp = 500
        self.max_hp = 500
        self.speed = 1.5  # Slower speed
        self.turn_speed = 1  # Slower turn speed - feels heavy and big
        self.color = 'boss'  # Purple color identifier
        self.shoot_cooldown = 0
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
