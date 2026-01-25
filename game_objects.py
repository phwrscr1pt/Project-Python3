import math


class Player:
    def __init__(self, x, y, color, angle=0, speed=0):
        self.x = x
        self.y = y
        self.color = color
        self.angle = angle  # 0-360 degrees
        self.speed = speed  # 0-8 max

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

    def get_state(self):
        return (self.x, self.y, self.angle, self.color)


class Bullet:
    def __init__(self, x, y, angle, speed=12):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed

    def move(self):
        angle_rad = math.radians(self.angle)
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed

    def is_out_of_bounds(self, width, height):
        return self.x < 0 or self.x > width or self.y < 0 or self.y > height
