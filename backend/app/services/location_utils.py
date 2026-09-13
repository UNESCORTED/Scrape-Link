def parse_lat_lon(location: str | None) -> tuple[float, float] | None:
    if not location:
        return None
    raw_lat, raw_lon = location.split(",", 1)
    latitude = float(raw_lat.strip())
    longitude = float(raw_lon.strip())
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("location is outside valid latitude/longitude range")
    return latitude, longitude
