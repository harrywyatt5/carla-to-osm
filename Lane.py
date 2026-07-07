from lxml import etree
from point import Point
import numpy as np

class Lane: 
    def __init__(self, parent, node):
        self._parent = parent
        self._node = node

    @property
    def id(self):
        return int(self._node.get("id"))

    @property
    def type(self):
        self._node.get("type")

    def sample_lane(self, step_size):
        num_samples = int(self._parent.road_length / step_size)
        samples = []

        for sample in np.linspace(0, self._parent.road_length, num_samples, endpoint=True):
            waypoint = self._parent._get_original_map().get_waypoint_xodr(self._parent.id, self.id, sample)
            samples.append(Point(waypoint.transform.x, -waypoint.transform.y))

        return samples
