from lxml import etree
from carla_to_osm.point import Point
import numpy as np

class Lane:
    _speed_limit_search_distance = 100

    def __init__(self, parent, node):
        self._parent = parent
        self._node = node

    @property
    def id(self):
        return int(self._node.get("id"))

    @property
    def type(self):
        self._node.get("type")

    @property
    def speed_limit(self):
        waypoint = self._parent._get_original_map().get_waypoint(self._parent.id, self.id, 0)

        speed_limit_landmarks = waypoint.get_landmarks_of_type(Lane._speed_limit_search_distance, 'speed_limit')
        if speed_limit_landmarks:
            return speed_limit_landmarks[0].value
        else:
            return None

    def sample_lane(self, step_size):
        num_samples = int(self._parent.road_length / step_size)
        samples = []

        for sample in np.linspace(0, self._parent.road_length, num_samples, endpoint=True):
            waypoint = self._parent._get_original_map().get_waypoint_xodr(self._parent.id, self.id, sample)
            samples.append(Point(waypoint.transform.x, -waypoint.transform.y))

        return samples
