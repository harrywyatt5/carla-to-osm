from carla_to_osm.way import SidewalkWay, CrosswalkWay, BuildingWay, WallWay, FenceWay, GuardRailWay
from carla_to_osm.point import BasicPoint, Point, TrafficLightCrossingPoint
import logging
import carla
import math
import numpy as np
from abc import ABC, abstractmethod
from functools import singledispatchmethod

logger = logging.getLogger(__name__)

class Polygon(ABC):
    def __init__(self, points):
        self._p0, self._p1, self._p2, self._p3 = Polygon._reorder_points(points)
        self._height = 0.0

        edge_1 = self._p0.get_distance(self._p1)
        edge_2 = self._p1.get_distance(self._p2)
        self._width = min(edge_1, edge_2)
        self._length = max(edge_1, edge_2)
        
        logger.debug("Polygon at %s, %s, %s, %s", self._p0, self._p1, self._p2, self._p3)

    @property
    def height(self):
        return self._height
    
    @property
    def length(self):
        return self._length
    
    @property
    def width(self):
        return self._width

    @abstractmethod
    def generate_points_and_way(self):
        raise NotImplementedError("Disallowed on base Polygon")

    @staticmethod
    def _reorder_points(points):
        if not points:
            return points
            
        cx = sum(p.x for p in points) / len(points)
        cy = sum(p.y for p in points) / len(points)
        return sorted(points, key=lambda p: math.atan2(p.y - cy, p.x - cx))

class CrosswalkPolygon(Polygon):
    _controller_distance = 10.0

    def __init__(self, args):
        super().__init__(args)

        # Midpoints of the edges
        mid_edge_a = self._p0.create_midpoint(self._p1)
        mid_edge_b = self._p1.create_midpoint(self._p2)
        mid_edge_c = self._p2.create_midpoint(self._p3)
        mid_edge_d = self._p3.create_midpoint(self._p0)

        # The walking path spans the longer dimension across the street.
        # So we connect the midpoints of the shorter edges.
        if self._p0.get_distance(self._p1) < self._p1.get_distance(self._p2):
            self._left = mid_edge_a
            self._right = mid_edge_c
        else:
            self._left = mid_edge_b
            self._right = mid_edge_d

        self._middle = self._left.create_midpoint(self._right)
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

class BuildingPolygon(Polygon):
    def __init__(self, bounding_box, transform):
        world_coords = bounding_box.get_world_vertices(transform)
        
        super().__init__([BasicPoint(coord.x, coord.y) for coord in world_coords[:4]])
        self._height = abs(world_coords[0].y - world_coords[4].y)

    def generate_points_and_way(self):
        points = list(map(lambda item : Point(item), [self._tl, self._tr, self._br, self._bl]))
        return BuildingWay(points + [points[0]], self._height)

class WallLikePolygon(Polygon):
    def __init__(self, bounding_box, transform):
        world_coords = bounding_box.get_world_vertices(transform)
        
        super().__init__([BasicPoint(coord.x, coord.y) for coord in world_coords[:4]])
        self._height = abs(world_coords[0].z - world_coords[4].z)
        self._top = self._tl.create_midpoint(self._tr)
        self._bottom = self._bl.create_midpoint(self._br)

    def generate_points_and_way(self):
        raise NotImplementedError("Use specialised function for specific ways")
    
    def _generate_points_and_way(self, class_type, step_size):
        distance = self._top.get_distance(self._bottom)
        num_samples = max(int(distance / step_size) + 1, 2)
        points = []

        for i in np.linspace(0, 1.0, num_samples, endpoint=True):
            x = self._bottom.x + i * (self._top.x - self._bottom.x)
            y = self._bottom.y + i * (self._top.y - self._bottom.y)
            points.append(Point(x, y))

        return class_type(points, self._height)

    def generate_points_and_fence_way(self, step_size):
        return self._generate_points_and_way(FenceWay, step_size)
    
    def generate_points_and_wall_way(self, step_size):
        return self._generate_points_and_way(WallWay, step_size)
    
    def generate_points_and_guard_rail_way(self, step_size):
        return self._generate_points_and_way(GuardRailWay, step_size)
