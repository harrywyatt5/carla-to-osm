from lxml import etree
import enum
import math

class WayType(enum.Enum):
    SIDEWALK = 0
    ROAD = 1
    CROSSWALK = 2

    def get_way_definition_tags(self):
        if self == WayType.SIDEWALK:
            return {
                "highway": "footway",
                "footway": "sidewalk"
            }
        elif self == WayType.ROAD:
            return {"highway": "residential"}
        else:
            return {
                "highway": "footway",
                "footway": "crosswalk"
            }


class Way:
    _global_way_count = 0

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
    def type(self):
        return self._type

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
    
    def join_other_ways(self, ways, max_distance, max_angle):
        if all(self._has_joined_ends) or not self.start_seg or not self.end_seg:
            return

        start_angle = self.start_seg[0].get_angle(self.start_seg[1])
        end_angle = self.end_seg[0].get_angle(self.end_seg[1])

        best_start_way, best_start_point, best_start_score = None, None, math.inf
        best_end_way, best_end_point, best_end_score = None, None, math.inf

        open_start_point = not self._has_joined_ends[0]
        open_end_point = not self._has_joined_ends[1]

        for way in ways:
            if way.type != self.type:
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
            new_way_for_start = Way._create_bridging_way(self.start, best_start_way, best_start_point, self.type)
            self._has_joined_ends = (True, self._has_joined_ends[1])
        
        if best_end_way:
            new_way_for_end = Way._create_bridging_way(self.end, best_end_way, best_end_point, self.type)
            self._has_joined_ends = (self._has_joined_ends[0], True)

        return (new_way_for_start, new_way_for_end)

    def __eq__(self, other):
        if not isinstance(self, Way):
            return NotImplemented
        
        return self.id == self.other

    def __hash__(self):
        return self.id

    @staticmethod
    def _create_bridging_way(source_point, target_way, target_point, way_type):
        if target_way.start == target_point:
            target_way._has_joined_ends = (True, target_way._has_joined_ends[1])
        else:
            target_way._has_joined_ends = (target_way._has_joined_ends[0], True)

        way = Way(way_type, [source_point, target_point])
        way._has_joined_ends = (True, True)
        return way

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
        # Determine type of lane
        lane_type = None
        if lane.type == "sidewalk":
            lane_type = WayType.SIDEWALK
        else:
            lane_type = WayType.ROAD

        samples = lane.sample_lane(step_size)
        return Way(lane_type, samples)

class RoadWay(Way):
    def __init__(self, nodes, lane_id, speed_limit):
        self._lane_id = lane_id
        self._speed_limit = speed_limit
        super().__init__(nodes)

    def get_way_tags(self):
        tags = {
            "highway": "residential",
            "sidewalk": "separate",
            "surface": "asphalt"
        }

        if self._speed_limit:
            tags["maxspeed"] = self._speed_limit + " mph"

        return tags
    
class PedWay(Way):
    def __init__(self, nodes):
        super().__init__(nodes)

    def get_way_tags(self):