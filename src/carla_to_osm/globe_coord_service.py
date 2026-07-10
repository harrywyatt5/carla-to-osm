from pyproj import CRS, Transformer

class GlobeCoordService:
    def __init__(self, origin_lat, origin_long):
        transform_str = \
            f"+proj=tmerc +lat_0={origin_lat} +lon_0={origin_long} " \
            + f"+k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        
        local_crs = CRS.from_proj4(transform_str)
        geo_crs = CRS.from_epsg(4326)
        self._transformer = Transformer.from_crs(local_crs, geo_crs, always_xy=True)

    def get_globe_coords(self, x, y):
        long, lat = self._transformer.transform(x, y)
        return (long, lat)
    
    def get_globe_coords_of_point(self, point):
        return self.get_globe_coords(point.x, point.y)
