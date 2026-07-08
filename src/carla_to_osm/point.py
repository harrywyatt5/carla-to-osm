import math

class Point:
    _global_node_count = 0

    def __init__(self, x, y):
        self._id = Point._global_node_count
        self._x = x
        self._y = y

        Point._global_node_count = Point._global_node_count + 1

    @property
    def id(self):
        return self._id

    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y
    
    def get_angle(self, other):
        return math.atan2(self.y - other.y, self.x - other.x)
    
    def get_distance(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented

        return self.id == other.id

    def __hash__(self):
        return id
