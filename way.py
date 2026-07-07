from lxml import etree
import enum

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
        pass

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
        
