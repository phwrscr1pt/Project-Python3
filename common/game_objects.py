import math


class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.color = color

    def move(self, inputs):
        # Rotation
        if inputs.get('left'):
            self.angle = (self.angle - 5) % 360
        if inputs.get('right'):
            self.angle = (self.angle + 5) % 360

        # Speed control
        if inputs.get('up'):
            self.speed = min(self.speed + 0.5, 10)
        if inputs.get('down'):
            self.speed = max(self.speed - 0.5, 0)

        # Movement based on angle
        angle_rad = math.radians(self.angle)
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed

    def get_data(self):
        return (self.x, self.y, self.angle, self.color)


class Bullet:
    def __init__(self, x, y, angle, speed=15):
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
