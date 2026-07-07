from lxml import etree
from lane import Lane

class Road:
    def __init__(self, map, node):
        self._map = map
        self._road_node = node
        self._lanes = None
        
        if not self._road_node.get("id") \
            or not self._road_node.get("length") \
            or not self._road_node.get("junction"):
            raise Exception("Not all Road properties are present. Aborting...")

    @property
    def id(self):
        return int(self._road_node.get("id"))
    
    @property
    def road_length(self):
        return float(self._road_node.get("length"))
    
    @property
    def junction(self):
        return int(self._road_node.get("junction"))
    
    @property
    def lanes(self):
        if self._lanes is None:
            self._lanes = [Lane(self, lane) for lane in self._road_node.findall(".//lanes")]

        return self._lanes
    
    def _get_original_map(self):
        return self._map

    def get_ped_lanes(self):
        return [lane for lane in self.lanes if lane.type == "sidewalk"]

    def get_driving_lanes(self):
        return [lane for lane in self.lanes if lane.type == "driving"]

    def is_junction(self):
        return self._road_node.get("junction") != "-1"
