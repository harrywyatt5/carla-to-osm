from lxml import etree
import logging
from carla_to_osm.road import Road
from carla_to_osm.polygon import Polygon, CrosswalkPolygon, BuildingPolygon, WallLikePolygon
from carla_to_osm.way import BuildingWay
from carla_to_osm.point import BasicPoint, Point
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
        return [BasicPoint(traffic_light.transform.location.x, -traffic_light.transform.location.y) for traffic_light in self._world.get_environment_objects(carla.CityObjectLabel.TrafficLight)]

    def get_map_crosswalks(self):
        carla_crosswalks = self._map.get_crosswalks()

        crosswalks = []
        point_cache = []
        for vertex in carla_crosswalks:
            # Z coord in Carla is up and down. We can ignore it as we are mapping to 2D plane.
            as_basic_point = BasicPoint(vertex.x, -vertex.y)

            if point_cache and as_basic_point.get_distance(point_cache[0]) < 0.01:
                logger.debug("Crosswalk at %s has %i points", as_basic_point, len(point_cache))
                crosswalks.append(CrosswalkPolygon(point_cache))
                point_cache = []
            else:
                point_cache.append(as_basic_point)

        return crosswalks

    def get_map_environmentals(self, step_size):
        environmentals = {}

        # Extract buildings
        buildings = self._world.get_environment_objects(carla.CityObjectLabel.Buildings)
        logger.info("Importing %i buildings", len(buildings))
        environmentals["buildings"] = [BuildingPolygon(building.bounding_box, building.transform).generate_points_and_way() for building in buildings]

        # Extract trees and bushes
        veg_objs = self._world.get_environment_objects(carla.CityObjectLabel.Vegetation)
        environmentals["vegetation"] = [Point.create_vegetation_point(veg) for veg in veg_objs]
        logger.info("Importing %i vegetation objects", len(environmentals["vegetation"]))

        # Extract poles?
        poles = self._world.get_environment_objects(carla.CityObjectLabel.Poles)
        environmentals["poles"] = [Point.create_pole_point(pole) for pole in poles]
        logger.info("Importing %i pole objects", len(environmentals["poles"]))

        # Extract guard rails, walls and fences
        fenses = self._world.get_environment_objects(carla.CityObjectLabel.Fences)
        walls = self._world.get_environment_objects(carla.CityObjectLabel.Walls)
        guard_rails = self._world.get_environment_objects(carla.CityObjectLabel.GuardRail)
        logger.info(
            "Importing %i wall-like objects. %i fenses. %i walls. %i guard rails",
            len(fenses) + len(walls) + len(guard_rails),
            len(fenses),
            len(walls),
            len(guard_rails)
        )
        environmentals["wall_like"] = [WallLikePolygon(fense.bounding_box, fense.transform).generate_points_and_fence_way(step_size) for fense in fenses] \
                                    + [WallLikePolygon(wall.bounding_box, wall.transform).generate_points_and_wall_way(step_size) for wall in walls] \
                                    + [WallLikePolygon(guard_rail.bounding_box, guard_rail.transform).generate_points_and_guard_rail_way(step_size) for guard_rail in guard_rails]

        return environmentals 
