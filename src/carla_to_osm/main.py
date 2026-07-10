from carla_to_osm.carla_server import CarlaServer
from carla_to_osm.way import Way, ACTIONABLE_WAYS
from carla_to_osm.globe_coord_service import GlobeCoordService
from carla_to_osm.osm_map import OsmMap
import argparse
import math

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
    return parser

def main() -> None:
    args = create_argparse_object().parse_args()

    server = CarlaServer(args.server, args.port, args.timeout)
    coord_service = GlobeCoordService(args.latitude, args.longitude)
    osm_map = OsmMap(coord_service, args.username)

    # Create ways from all our roads / lanes
    roads = server.get_map_roads()
    print(f"We have {len(roads)} roads!")
    ways = [Way.create_way_from_lane(lane, args.step_size) for road in roads for lane in road.lanes if lane.type in ACTIONABLE_WAYS]

    print(f"We have {len(ways)} ways!")

    # See if any of our ways can be connected up together
    angle_in_radians = math.radians(args.max_angle)
    new_ways = []
    for way in ways:
        ways_tuple = way.join_other_ways(ways, args.max_distance, angle_in_radians)
        new_ways = new_ways + [unpacked_way for unpacked_way in ways_tuple if unpacked_way]

    ways = ways + new_ways

    osm_map.add_ways(ways)

    # TODO: crosswalk logic
    # TODO: building logic

    osm_map.build_and_write(args.output_file)
    print(f"Success! File written to {args.output_file}")

if __name__ == "__main__":
    main()
