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
    def __init__(self, way_type, nodes):
        self._type = way_type
        self._nodes = nodes
        self._start = nodes[0]
        self._end = nodes[-1]
        self._has_joined_ends = (False, False)

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
        
        return self._nodes[:2]
    
    @property
    def end_seg(self):
        if len(self._nodes) < 2:
            return []
        
        return self._nodes[-2:]

    @property
    def nodes(self):
        return self._nodes
    
    def try_join_to_other_ways(self, ways, max_radius, max_angle):
        # If both ends of this way have already been joined up, then let's just not do this
        if self._has_joined_ends[0] and self._has_joined_ends[1]:
            return (None, None)
        
        # If our way is long enough...
        start_seg = self.start_seg
        end_seg = self.end_seg
        if not start_seg or not end_seg:
            return (None, None)
        
        start_angle = start_seg[0].get_angle(start_seg[1])
        end_angle = end_seg[0].get_angle(end_seg[1])

        start_new_way = None
        end_new_way = None

        best_way = [None, None]
        best_distance = [math.inf, math.inf]
        best_angle = [math.inf, math.inf]
        for way in ways:
            # Compare with the start way, if it's not already been joined up
            if not self._has_joined_ends[0]:
                # Compare to its start node
                if not way._has_joined_ends[0]:
                    distance, angle = Way._compare_segment(start_angle, self.start, way.start, way.start_seg)

    @staticmethod
    def _compare_segment(target_angle, target_point, other_point, other_segment):
        if not other_segment:
            return (math.inf, math.inf)
        
        other_angle = other_segment[0].get_angle(other_segment[1])
        distance = target_point.get_distance(other_point)

        angle = abs(target_angle - other_angle) % math.pi
        if angle > (math.pi / 2):
            angle = math.pi - angle

        return (distance, angle)

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
        
