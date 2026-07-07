from lxml import etree

class Road:
    def __init__(self, node):
        self._road_node = node
        
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

    def is_junction(self):
        return self._road_node.get("junction") != "-1"
