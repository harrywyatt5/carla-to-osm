import math
import logging
from functools import singledispatchmethod

logger = logging.getLogger(__name__)

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

        delta = 0.01
        return self.x - other.x < delta and self.y - other.y < delta
    
    def __hash__(self):
        return hash(f"{self.x:.3f}:{self.y:.3f}")
    
    def __str__(self):
        return f"({self.x:.3f}, {self.y:.3f})"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y})"

class Point(BasicPoint):
    _global_node_count = 1

    @singledispatchmethod
    def __init__(self, x, y):
        super().__init__(x, y)
        self._id = Point._global_node_count
        Point._global_node_count = Point._global_node_count + 1

    @__init__.register
    def _(self, point: BasicPoint):
        super().__init__(point.x, point.y)
        self._id = Point._global_node_count
        Point._global_node_count = Point._global_node_count + 1

    def get_point_tags(self):
        return {}

    @property
    def id(self):
        return self._id
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented

        return self.id == other.id

    def __hash__(self):
        return hash(int(self.id))
    
    @staticmethod
    def create_vegetation_point(enviroment_object):
        # Get height and width
        width = max(enviroment_object.bounding_box.extent.x * 2.0, enviroment_object.bounding_box.extent.y * 2.0)
        height = enviroment_object.bounding_box.extent.z * 2.0

        cls = TreePoint if "tree" in enviroment_object.name.lower() else BushPoint
        return cls(enviroment_object.transform.location.x, enviroment_object.transform.location.y, width, height)
    
    @staticmethod
    def create_pole_point(environment_object):
        height = environment_object.bounding_box.extent.z * 2.0

        name = environment_object.name.lower()
        cls = LightPoint if "light" in name or "lamp" in name else PolePoint
        return cls(environment_object.transform.location.x, environment_object.transform.location.y, height)

class TrafficLightCrossingPoint(Point):
    @singledispatchmethod
    def __init__(self, x, y):
        super().__init__(x, y)

    @__init__.register
    def _(self, point: BasicPoint):
        super().__init__(point.x, point.y)

    @__init__.register
    def _(self, point: Point):
        logger.debug("Point being upgraded to TrafficLightCrossingPoint. It will share the same ID")
        self._x = point.x
        self._y = point.y
        self._id = point.id

    def get_point_tags(self):
        return {
            "crossing": "traffic_signals",
            "crossing:island": "no",
            "crossing:signals": "yes",
            "crossing_ref": "pelican",
            "highway": "crossing"
        }

class TreePoint(Point):
    def __init__(self, x, y, width, height):
        super().__init__(x, y)
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width
    
    @property
    def height(self):
        return self._height

    def get_point_tags(self):
        return {
            "natural": "tree",
            "diameter_crown": f"{self._width:.2f}",
            "height": f"{self._height:.2f}"
        }
    
class BushPoint(TreePoint):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

    def get_point_tags(self):
        return {
            "natural": "bush",
            "diameter_crown": f"{self._width:.2f}",
            "height": f"{self._height:.2f}"
        }

class PolePoint(Point):
    def __init__(self, x, y, height):
        self._height = height
        super().__init__(x, y)

    def get_point_tags(self):
        return {
            "man_made": "utility_pole",
            "height": f"{self._height:.2f}"
        }
    
class LightPoint(Point):
    def __init__(self, x, y, height):
        self._height = height
        super().__init__(x, y)

    def get_point_tags(self):
        return {
            "highway": "street_lamp",
            "lamp_mount": "pole",
            "height": f"{self._height:.2f}"
        }
