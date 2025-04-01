import random
from math import radians, sin, cos, sqrt

def generate_random_neighbour(lat, lon, max_distance_km):
    """Generate more evenly distributed random locations within radius"""
    earth_radius_km = 6371.0
    
    # Convert max distance to degrees (more accurate calculation)
    lat_diff = max_distance_km / earth_radius_km
    lon_diff = max_distance_km / (earth_radius_km * cos(radians(lat)))
    
    # Use polar coordinates for more uniform distribution
    r = random.uniform(0, max_distance_km) * sqrt(random.random())
    theta = random.uniform(0, 2 * 3.141592653589793)
    
    # Convert polar to Cartesian offsets
    lat_offset = (r * cos(theta)) / earth_radius_km
    lon_offset = (r * sin(theta)) / (earth_radius_km * cos(radians(lat)))
    
    new_lat = lat + lat_offset
    new_lon = lon + lon_offset
    
    # Ensure coordinates stay within valid ranges
    new_lat = max(-90, min(90, new_lat))
    new_lon = max(-180, min(180, new_lon))
    
    return new_lat, new_lon

def add_random_location(data, given_lat, given_lon, max_distance_km):
    """Add random locations with better clustering control"""
    # Generate cluster centers first
    cluster_centers = []
    for _ in range(random.randint(1, 3)):  # 1-3 cluster centers
        center_lat, center_lon = generate_random_neighbour(given_lat, given_lon, max_distance_km/2)
        cluster_centers.append((center_lat, center_lon))
    
    for frame in data:
        for detection in frame['detections']:
            # Choose a random cluster center for this detection
            center_lat, center_lon = random.choice(cluster_centers)
            
            # Generate location near the cluster center
            new_lat, new_lon = generate_random_neighbour(center_lat, center_lon, max_distance_km/4)
            
            # Ensure it's within max distance from original point
            while sqrt((new_lat - given_lat)**2 + (new_lon - given_lon)**2) > max_distance_km:
                new_lat, new_lon = generate_random_neighbour(center_lat, center_lon, max_distance_km/4)
            
            detection['latitude'] = new_lat
            detection['longitude'] = new_lon
    
    return data