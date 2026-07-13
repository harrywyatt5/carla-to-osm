import math

class BasicPoint:
    def __init__(self, x, y):
        self._x = x
        self._y = y

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
    
    def create_midpoint(self, other):
        return self.__class__((self.x + other.x) / 2, (self.y + other.y) / 2)
    
    def __eq__(self, other):
        if not isinstance(other, BasicPoint):
            return NotImplemented

        delta = 0.001
        return self.x - other.x < delta and self.y - other.y < delta
    
    def __hash__(self):
        return hash(f"{self.x:.3f}:{self.y:.3f}")
    
    def __repr__(self):
        return f"({self.x:.3f}, {self.y:.3f})"

class Point(BasicPoint):
    _global_node_count = 1

    def __init__(self, x, y):
        super().__init__(x, y)
        self._id = Point._global_node_count
        Point._global_node_count = Point._global_node_count + 1

    def __init__(self, point):
        super().__init__(point.x, point.y)
        self._id = Point._global_node_count
        Point._global_node_count = Point._global_node_count + 1

    @property
    def id(self):
        return self._id
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented

        return self.id == other.id

    def __hash__(self):
        return hash(int(self.id))
