import math

from models.schemas import Coordinates

EARTH_RADIUS = 6371000


def distance(a: Coordinates, b: Coordinates) -> float:
    p, q = math.radians(a.latitude), math.radians(b.latitude)
    dp = q - p
    dl = math.radians(b.longitude - a.longitude)
    h = math.sin(dp / 2) ** 2 + math.cos(p) * math.cos(q) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(min(1, max(0, h))))


def bearing(a: Coordinates, b: Coordinates) -> float:
    p, q = math.radians(a.latitude), math.radians(b.latitude)
    dl = math.radians(b.longitude - a.longitude)
    return (
        math.degrees(
            math.atan2(
                math.sin(dl) * math.cos(q),
                math.cos(p) * math.sin(q) - math.sin(p) * math.cos(q) * math.cos(dl),
            )
        )
        % 360
    )


def destination(start: Coordinates, heading: float, meters: float) -> Coordinates:
    p, longitude, h = map(math.radians, (start.latitude, start.longitude, heading))
    d = meters / EARTH_RADIUS
    q = math.asin(max(-1, min(1, math.sin(p) * math.cos(d) + math.cos(p) * math.sin(d) * math.cos(h))))
    r = longitude + math.atan2(
        math.sin(h) * math.sin(d) * math.cos(p), math.cos(d) - math.sin(p) * math.sin(q)
    )
    return Coordinates(latitude=math.degrees(q), longitude=(math.degrees(r) + 180) % 360 - 180)
