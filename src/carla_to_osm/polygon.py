from carla_to_osm.way import SidewalkWay, CrosswalkWay
from carla_to_osm.point import Point, TrafficLightCrossingPoint
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
    _controller_distance = 5.0

    def __init__(self, *args):
        super().__init__(*args)

        # For a crosswalk, we create a line through the middle of the polygon
        self._left = self._tl.create_midpoint(self._bl)
        self._middle = self._tl.create_midpoint(self._br)
        self._right = self._tr.create_midpoint(self._br)

        self._has_traffic_light = False

        self._left_connection = None
        self._right_connection = None

    def try_associate_controller(self, controller):
        points = [self._left, self._middle, self._right]

        if any(point.get_distance(controller) < CrosswalkPolygon._controller_distance for point in points):
            logger.debug("Traffic light at %s successfully associated to crosswalk", controller)
            self._has_traffic_light = True
            return True
        else:
            return False

    def connect_to_other_ways(self, other_ways):
        left_connecting_point, left_connecting_distance = None, math.inf
        right_connecting_point, right_connecting_distance = None, math.inf

        for way in other_ways:
            # Skip ways which are not for people
            if not isinstance(way, SidewalkWay):
                continue
            
            # We assume that there is at least one point in the entire set of ways
            for point in way.nodes:
                distance_to_left = point.get_distance(self._left)
                distance_to_right = point.get_distance(self._right)

                if distance_to_left < left_connecting_distance:
                    left_connecting_point = point
                    left_connecting_distance = distance_to_left

                if distance_to_right < right_connecting_distance:
                    right_connecting_point = point
                    right_connecting_distance = distance_to_right
        
        logger.debug(
            "Connected crosswalk to point %i (with distance %fm) and point %i (with distance %fm)",
            left_connecting_point.id,
            left_connecting_distance,
            right_connecting_point.id,
            right_connecting_distance
        )

        self._left_connection = left_connecting_point
        self._right_connection = right_connecting_point

    def generate_points_and_way(self):
        if not self._left_connection or not self._right_connection:
            logger.warning("Not connected to other Ways. This likely will mean the crosswalk is disconnected from the rest of the map")

        crosswalk_points = [
            self._left_connection,
            Point(self._left),
            Point(self._middle) if not self._has_traffic_light else TrafficLightCrossingPoint(self._middle),
            Point(self._right),
            self._right_connection
        ]
        crosswalk_points = [point for point in crosswalk_points if point is not None]

        return CrosswalkWay(crosswalk_points)
