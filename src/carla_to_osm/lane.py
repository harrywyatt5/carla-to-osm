from lxml import etree
from carla_to_osm.point import Point
import numpy as np

class Lane:
    _speed_limit_search_distance = 100

    def __init__(self, parent, node):
        self._parent = parent
        self._speed_limit = None
        self._node = node

    @property
    def id(self):
        return int(self._node.get("id"))

    @property
    def type(self):
        return self._node.get("type")

    @property
    def speed_limit(self):
        if self._speed_limit:
            return self._speed_limit

        road_length = self._parent.road_length
        sample_point = [0.0, 0.25 * road_length, 0.5 * road_length, 0.75 * road_length, 0.9 * road_length, road_length]

        # Try and find ANYYY waypoint we can sample from
        golden_waypoint = None
        for sample in sample_point:
            golden_waypoint = self._parent._get_original_map().get_waypoint_xodr(self._parent.id, self.id, sample)

            if golden_waypoint:
                break
        
        if not golden_waypoint:
            return None

        speed_limit_landmarks = golden_waypoint.get_landmarks_of_type(Lane._speed_limit_search_distance, 'speed_limit')
        if speed_limit_landmarks:
            self._speed_limit = speed_limit_landmarks[0].value
            return self._speed_limit
        else:
            return None

    def sample_lane(self, step_size):
        num_samples = max(2, int(self._parent.road_length / step_size) + 1)
        samples = []

        for sample in np.linspace(0, self._parent.road_length, num_samples, endpoint=True):
            waypoint = self._parent._get_original_map().get_waypoint_xodr(self._parent.id, self.id, sample)

            # Sometimes lanes don't exist for the whole duration of the road...
            if waypoint is None:
                continue

            samples.append(Point(waypoint.transform.location.x, -waypoint.transform.location.y))

        return samples
