import json
from shapely.geometry import Point, Polygon
def check_location():
    with open("areamap.json", "r") as f:
        poly_coords_dict=json.load(f)
        f.close()
    polygon_vertices = []
    for lat_str, lon_str in poly_coords_dict.items():
        lon_float = float(lon_str)
        lat_float = float(lat_str)
        polygon_vertices.append((lon_float, lat_float)) # Append as (lon, lat)
    
    point_lat_float,point_lon_float = [float(x) for x in (input("Enter the coordinates : ").split(","))]

    test_point_tuple = (point_lon_float, point_lat_float) # Store as (lon, lat)
    polygon = Polygon(polygon_vertices)    
    point = Point(test_point_tuple)
    is_inside = polygon.contains(point)
    touches_boundary = polygon.touches(point)
    if is_inside:
        return True
    elif touches_boundary:
        return True
    else:
        return False

print(check_location())