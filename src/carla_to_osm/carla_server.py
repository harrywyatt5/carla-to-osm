from lxml import etree
from carla_to_osm.road import Road
try:
    import carla
except ImportError:
    raise ImportError("Could not find carla package. "
                      "Ensure to run uv sync --extra carla if are running 0.9.16. "
                      "Otherwise, install a custom wheel using uv pip install ./custom-carla-wheel.whl")

class CarlaServer:
    def __init__(self, server_ip: str, port: int, max_timeout: float):
        self._server = carla.Client(server_ip, port)
        self._server.set_timeout(max_timeout)
        self._world = self._server.get_world()
        self._map = self._world.get_map()
    
    def get_map_roads(self):
        opendrive_map = etree.fromstring(self._map.to_opendrive().encode("utf-8"))
        return [Road(self._map, road) for road in opendrive_map.findall("road")] 

    def get_map_crosswalks(self):
        pass

    def get_map_environmentals(self):
        pass
