from lxml import etree

class OsmMap:
    def __init__(self):
        self._root = etree.Element("osm", version=0.6, generator="carla_to_osm")
        self._ways = set()
        self._nodes = set()

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
        pass

    def build_and_write(self, dest):
        pass
