from lxml import etree
from carla_to_osm.point import Point
import math
import logging

logger = logging.getLogger(__name__)

ACTIONABLE_WAYS = [
    "driving",
    "sidewalk"
]

class Way:
    _global_way_count = 1

    def __init__(self, nodes):
        self._id = Way._global_way_count
        self._nodes = nodes
        self._start = nodes[0]
        self._end = nodes[-1]
        self._start_seg = []
        self._end_seg = []
        self._has_joined_ends = (False, False)

        Way._global_way_count = Way._global_way_count + 1

    @property
    def id(self):
        return self._id

    @property
    def start(self):
        return self._start
    
    @property
    def end(self):
        return self._end

    @property
    def start_seg(self):
        if len(self._nodes) < 2:
            return []
        
        if not self._start_seg:
            self._start_seg = self._nodes[:2]
        
        return self._start_seg
    
    @property
    def end_seg(self):
        if len(self._nodes) < 2:
            return []
        
        if not self._end_seg:
            self._end_seg = self._nodes[-2:]
        
        return self._end_seg

    @property
    def nodes(self):
        return self._nodes
    
    def get_way_tags(self):
        return {}
    
    def join_other_ways(self, ways, max_distance, max_angle):
        if all(self._has_joined_ends) or not self.start_seg or not self.end_seg:
            return (None, None)

        start_angle = self.start_seg[0].get_angle(self.start_seg[1])
        end_angle = self.end_seg[0].get_angle(self.end_seg[1])

        best_start_way, best_start_point, best_start_score = None, None, math.inf
        best_end_way, best_end_point, best_end_score = None, None, math.inf

        open_start_point = not self._has_joined_ends[0]
        open_end_point = not self._has_joined_ends[1]

        for way in ways:
            # Don't compare different types of ways or the exact same way haha
            if way == self or type(way) != type(self):
                continue

            if not way._has_joined_ends[0]:
                if open_start_point:
                    best_start_way, best_start_point, best_start_score = self._evaluate_candidate(
                        best_start_way, best_start_point, best_start_score,
                        self.start, start_angle, way, way.start, way.start_seg,
                        max_distance, max_angle
                    )

                if open_end_point:
                    best_end_way, best_end_point, best_end_score = self._evaluate_candidate(
                        best_end_way, best_end_point, best_end_score,
                        self.end, end_angle, way, way.start, way.start_seg,
                        max_distance, max_angle
                    )

            if not way._has_joined_ends[1]:
                if open_start_point:
                    best_start_way, best_start_point, best_start_score = self._evaluate_candidate(
                        best_start_way, best_start_point, best_start_score,
                        self.start, start_angle, way, way.end, way.end_seg,
                        max_distance, max_angle
                    )
                
                if open_end_point:
                    best_end_way, best_end_point, best_end_score = self._evaluate_candidate(
                        best_end_way, best_end_point, best_end_score,
                        self.end, end_angle, way, way.end, way.end_seg,
                        max_distance, max_angle
                    )
        
        new_way_for_start = None
        new_way_for_end = None
        if best_start_way:
            new_way_for_start = self._create_bridging_way(self.start, best_start_way, best_start_point)
            self._has_joined_ends = (True, self._has_joined_ends[1])
        
        if best_end_way:
            new_way_for_end = self._create_bridging_way(self.end, best_end_way, best_end_point)
            self._has_joined_ends = (self._has_joined_ends[0], True)

        return (new_way_for_start, new_way_for_end)

    def _create_bridging_way(self, source_point, target_way, target_point):
        if target_way.start == target_point:
            target_way._has_joined_ends = (True, target_way._has_joined_ends[1])
        else:
            target_way._has_joined_ends = (target_way._has_joined_ends[0], True)

        way = None
        if isinstance(self, RoadWay):
            way = RoadWay([source_point, target_point], self._lane_id, self._speed_limit)
        else:
            way = self.__class__([source_point, target_point])

        way._has_joined_ends = (True, True)
        return way

    def __eq__(self, other):
        if not isinstance(self, Way):
            return NotImplemented
        
        return self.id == other.id

    def __hash__(self):
        return hash(int(self.id))

    @staticmethod
    def _evaluate_candidate(best_way, best_point, best_score,
                            target_point, target_angle,
                            cand_way, cand_point, cand_seg,
                            max_dist, max_angle):
        if not cand_seg:
            return (best_way, best_point, best_score)
        
        cand_angle = cand_seg[0].get_angle(cand_seg[1])
        distance = target_point.get_distance(cand_point)

        diff_in_angle = abs(target_angle - cand_angle) % math.pi
        if diff_in_angle > (math.pi / 2):
            diff_in_angle = math.pi - diff_in_angle

        if distance > max_dist or diff_in_angle > max_angle:
            return (best_way, best_point, best_score)
        
        norm_distance = distance / max_dist
        norm_angle = diff_in_angle / max_angle
        score = (3.0 * norm_distance) + (1.0 * norm_angle)

        if score < best_score:
            return (cand_way, cand_point, score)
        
        return (best_way, best_point, best_score)
        
    @staticmethod
    def create_way_from_lane(lane, step_size):
        samples = lane.sample_lane(step_size)

        if lane.type == "sidewalk":
            return SidewalkWay(samples)
        elif lane.type == "driving":
            return RoadWay(samples, lane.id, lane.speed_limit)
        else:
            logger.warning("Unknown road type '%s'. Skipping", lane.type)
            return None

class RoadWay(Way):
    def __init__(self, nodes, lane_id, speed_limit):
        self._lane_id = lane_id
        self._speed_limit = speed_limit
        super().__init__(nodes)

    def get_way_tags(self):
        tags = {
            "highway": "residential",
            "lane_id": str(self._lane_id),
            "sidewalk": "separate",
            "surface": "asphalt"
        }

        if self._speed_limit:
            tags["maxspeed"] = self._speed_limit + " mph"

        return tags
    
class SidewalkWay(Way):
    def __init__(self, nodes):
        super().__init__(nodes)

    def get_way_tags(self):
        return {
            "highway": "footway",
            "footway": "sidewalk"
        }
    
class CrosswalkWay(Way):
    def __init__(self, nodes):
        super().__init__(nodes)

    def get_way_tags(self):
        return {
            "highway": "footway",
            "footway": "crosswalk"
        }
    
    def join_other_ways(self, ways, max_distance, max_angle):
        raise NotImplementedError("join_other_ways is not possible on a Crosswalk object")

class BuildingWay(Way):
    _floor_height = 3.5

    def __init__(self, points, height):
        super().__init__(points)
        self._height = height

    def get_way_tags(self):
        return {
            "building": "yes",
            "building:levels": f"{(self._height / BuildingWay._floor_height):.2f}",
            "height": f"{self._height:.2f}"
        }

class FenceWay(Way):
    def __init__(self, nodes, height):
        super().__init__(nodes)
        self._height = height

    def get_way_tags(self):
        return {
            "barrier": "fence",
            "height": f"{self._height:.2f}"
        }

class WallWay(Way):
    def __init__(self, nodes, height):
        super().__init__(nodes)
        self._height = height

    def get_way_tags(self):
        return {
            "barrier": "wall",
            "height": f"{self._height:.2f}"
        }

class GuardRailWay(Way):
    def __init__(self, nodes, height):
        super().__init__(nodes)
        self._height = height

    def get_way_tags(self):
        return {
            "barrier": "guard_rail"
        }
