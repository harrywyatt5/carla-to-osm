import carla
from lxml import etree

class CarlaServer:
    def __init__(self, server_ip: str, port: int, max_timeout: float):
        self._server = carla.Client(server_ip, port)
        self._server.set_timeout(max_timeout)
        self._world = self._server.get_world()
        self._map = self._world.get_map()
    
    def get_opendrive_world(self):
        map = etree.fromstring(self._map.to_opendrive().encode("utf-8"))