from lxml import etree

class OsmMap:
    def __init__(self, coord_service, username):
        self._root = etree.Element("osm", version=0.6, generator="carla_to_osm")
        self._ways = set()
        self._nodes = set()
        self._coord_service = coord_service
        self._username = username

    def add_ways(self, ways):
        for way in ways:
            if way in self._ways:
                print("Duplicate way detected!")
                continue

            self._ways.add(way)
            self.add_nodes(way.nodes)

    def add_nodes(self, nodes):
        self._nodes = self._nodes | set(nodes)

    def build(self):
        # Generate points as nodes
        for point in self._nodes:
            long, lat = self._coord_service.get_globe_coords(point.x, point.y)
            etree.SubElement(self._root, "node", id=str(point.id), visible="true", lat=str(lat), lon=str(long))

        # Generate ways 


    def build_and_write(self, dest):
        pass
