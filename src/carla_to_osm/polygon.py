from carla_to_osm.way import SidewalkWay, CrosswalkWay
import logging
import math
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class Polygon(ABC):
    def __init__(self, *args):
        self._tl, self._tr, self._bl, self._br = Polygon._reorder_points(args)
        logger.debug("Polygon at %s, %s, %s, %s", self._tl, self._tr, self._bl, self._br)

    @abstractmethod
    def generate_points_and_way(self):
        raise NotImplementedError("Disallowed on base Polygon")

    @staticmethod
    def _reorder_points(points):
        sort_by_x = sorted(points, lambda item : item.x)

        left_points = sort_by_x[:2]
        right_points = sort_by_x[2:]

        # Sort by Y
        top_left, bottom_left = sorted(left_points, lambda item : item.y)
        top_right, bottom_right = sorted(right_points, lambda item : item.y)
        return (top_left, top_right, bottom_left, bottom_right)

class CrosswalkPolygon(Polygon):
    def __init__(self, *args):
        super().__init__(*args)
        self._is_connected = False

        # For a crosswalk, we create a line through the middle of the polygon
        self._left = self._tl.create_midpoint(self._bl)
        self._middle = self._tl.create_midpoint(self._br)
        self._right = self._tr.create_midpoint(self._br)

    def connect_to_other_ways(self, other_ways):
        left_connecting_point, left_connecting_distance = None, math.inf
        right_connecting_point, right_connecting_distance = None, math.inf

        for way in other_ways:
            # Skip ways which are not for people
            if not isinstance(way, SidewalkWay):
                continue




    def generate_points_and_way(self):
        if not self._is_connected:
            logger.warning("Not connected to other Ways. This likely will mean the crosswalk is disconnected from the rest of the map")