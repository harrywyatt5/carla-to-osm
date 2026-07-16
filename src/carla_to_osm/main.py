from carla_to_osm.carla_server import CarlaServer
from carla_to_osm.way import Way, CrosswalkWay, ACTIONABLE_WAYS
from carla_to_osm.polygon import CrosswalkPolygon
from carla_to_osm.globe_coord_service import GlobeCoordService
from carla_to_osm.osm_map import OsmMap
from carla_to_osm.point import BasicPoint
import argparse
import math
import time
import logging

logger = logging.getLogger(__name__)

def create_argparse_object() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Converts from CARLA maps currently open to a OpenStreetMaps file")
    parser.add_argument("-o", "--output_file", required=False, type=str, default="./map.osm")
    parser.add_argument("-s", "--server", required=False, type=str, default="127.0.0.1")
    parser.add_argument("-n", "--step_size", required=False, type=float, default=0.5)
    parser.add_argument("-p", "--port", required=False, type=int, default=2000)
    parser.add_argument("-t", "--timeout", required=False, type=float, default=10.0)
    parser.add_argument("-d", "--max_distance", required=False, type=float, default=5.0)
    parser.add_argument("-a", "--max_angle", required=False, type=float, default=30.0)
    parser.add_argument("-l", "--longitude", required=False, type=float, default=-0.1263935)
    parser.add_argument("-k", "--latitude", required=False, type=float, default=51.5053592)
    parser.add_argument("-c", "--username", required=False, type=str, default="WyattH4")
    parser.add_argument("-e", "--log_level", required=False, type=str, default="info")
    return parser

def get_logging_level(level: str) -> int:
    level_low = level.lower()

    if level_low == "debug":
        return logging.DEBUG
    elif level_low == "info":
        return logging.INFO
    elif level_low == "warn" or level_low == "warning":
        return logging.WARN
    elif level_low == "error":
        return logging.ERROR
    elif level_low == "critical":
        return logging.CRITICAL
    else:
        logger.warning("Could not recognise log level of '%s'", level)
        return logging.NOTSET
    
def _build_crosswalk(crosswalk_polygon: CrosswalkPolygon, other_ways: list[Way], traffic_lights: list[BasicPoint]) -> CrosswalkWay:
    any(crosswalk_polygon.try_associate_controller(traffic_light) for traffic_light in traffic_lights)
    crosswalk_polygon.connect_to_other_ways(other_ways)
    return crosswalk_polygon.generate_points_and_way()

def main() -> None:
    start_time = time.time_ns()

    args = create_argparse_object().parse_args()
    logging.basicConfig(
        level=get_logging_level(args.log_level)
    )

    server = CarlaServer(args.server, args.port, args.timeout)
    coord_service = GlobeCoordService(args.latitude, args.longitude)
    osm_map = OsmMap(coord_service, args.username)

    # Create ways from all our roads / lanes
    roads = server.get_map_roads()
    logger.debug("%i roads resolved from CARLA", len(roads))
    ways = [Way.create_way_from_lane(lane, args.step_size) for road in roads for lane in road.lanes if lane.type in ACTIONABLE_WAYS]

    logger.debug("%i ways generated from roads", len(ways))

    # See if any of our ways can be connected up together
    angle_in_radians = math.radians(args.max_angle)
    new_ways = []
    for way in ways:
        ways_tuple = way.join_other_ways(ways, args.max_distance, angle_in_radians)
        new_ways = new_ways + [unpacked_way for unpacked_way in ways_tuple if unpacked_way]

    logger.debug("Found %i new connections", len(new_ways))
    ways = ways + new_ways

    osm_map.add_ways(ways)

    # Crosswalk logic
    crosswalks = server.get_map_crosswalks()
    traffic_lights = server.get_map_traffic_lights()
    crosswalk_ways = [_build_crosswalk(crosswalk, ways, traffic_lights) for crosswalk in crosswalks]
    logger.info("Created %i crosswalks", len(crosswalk_ways))
    osm_map.add_ways(crosswalk_ways)

    # TODO: building logic


    osm_map.build_and_write(args.output_file)
    logger.info(f"Success! File written to {args.output_file}")
    logger.info(f"Took {((time.time_ns() - start_time) / 1_000_000)} ms to complete")

if __name__ == "__main__":
    main()
