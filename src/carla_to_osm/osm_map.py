from lxml import etree
import logging

logger = logging.getLogger(__name__)

class OsmMap:
    def __init__(self, coord_service, username):
        self._root = etree.Element("osm", version="0.6", generator="carla_to_osm")
        self._ways = set()
        self._nodes = set()
        self._coord_service = coord_service
        self._username = username

    def add_ways(self, ways):
        for way in ways:
            if way in self._ways:
                logger.warning("Duplicate way detected!")
                continue

            self._ways.add(way)
            self.add_nodes(way.nodes)

    def add_nodes(self, nodes):
        self._nodes = self._nodes | set(nodes)

    def build(self):
        # Generate points as nodes
        for point in self._nodes:
            long, lat = self._coord_service.get_globe_coords(point.x, point.y)
            etree.SubElement(self._root, "node", id=str(point.id), version="1", changeset="1", visible="true", user=str(self._username), lat=str(lat), lon=str(long))

        # Generate ways
        for way in self._ways:
            way_xml_node = etree.SubElement(self._root, "way", id=str(way.id), version="1", changeset="1", visible="true", user=str(self._username))

            for point in way.nodes:
                etree.SubElement(way_xml_node, "nd", ref=str(point.id))

            for key, value in way.get_way_tags().items():
                etree.SubElement(way_xml_node, "tag", k=str(key), v=str(value))

        return self._root

    def build_and_write(self, dest, pretty_print=True):
        tree = etree.ElementTree(self.build())
        tree.write(dest, pretty_print=pretty_print, xml_declaration=True, encoding="UTF-8")
