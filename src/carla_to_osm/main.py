import argparse

def create_argparse_object() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Converts from CARLA maps currently open to a OpenStreetMaps file")
    parser.add_argument("-o", "--output_file", required=False, type=str, default="./map.osm")
    parser.add_argument("-s", "--server", required=False, type=str, default="127.0.0.1")
    parser.add_argument("-p", "--port", required=False, type=int, default=2000)
    return parser

def main() -> None:
    args = create_argparse_object().parse_args()
    print("Hello from carlatoosm!")

if __name__ == "__main__":
    main()
