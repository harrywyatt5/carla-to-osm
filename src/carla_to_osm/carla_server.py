from lxml import etree
import logging
from carla_to_osm.road import Road
from carla_to_osm.polygon import Polygon, CrosswalkPolygon
from carla_to_osm.point import BasicPoint
try:
    import carla
except ImportError:
    raise ImportError("Could not find carla package. "
                      "Ensure to run uv sync --extra carla if you are running 0.9.16. "
                      "Otherwise, install a custom wheel using uv pip install ./custom-carla-wheel.whl")

logger = logging.getLogger(__name__)

class CarlaServer:
    def __init__(self, server_ip: str, port: int, max_timeout: float):
        self._server = carla.Client(server_ip, port)
        self._server.set_timeout(max_timeout)
        self._world = self._server.get_world()
        self._map = self._world.get_map()
    
    def get_map_roads(self):
        opendrive_map = etree.fromstring(self._map.to_opendrive().encode("utf-8"))
        return [Road(self._map, road) for road in opendrive_map.findall("road")]
    
    def get_map_traffic_lights(self):
        traffic_lights = self._world.get_environment_objects(carla.CityObjectLabel.TrafficLight)

    def get_map_crosswalks(self):
        carla_crosswalks = self._map.get_crosswalks()

        crosswalks = []
        point_cache = []
        for vertex in carla_crosswalks:
            # Z coord in Carla is up and down. We can ignore it as we are mapping to 2D plane.
            as_basic_point = BasicPoint(vertex.x, vertex.y)

            if as_basic_point.get_distance(point_cache[0]) < 0.01:
                logger.debug("Crosswalk at %s has %i points", as_basic_point, len(point_cache))
                crosswalks.append(CrosswalkPolygon(point_cache))
                point_cache = []
            else:
                point_cache.append(as_basic_point)

        return crosswalks

    def get_map_environmentals(self):
        pass
