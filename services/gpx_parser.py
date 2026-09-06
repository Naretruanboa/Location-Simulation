from defusedxml import ElementTree

from models.schemas import Coordinates


def parse_gpx(xml: str) -> list[Coordinates]:
    try:
        root = ElementTree.fromstring(xml)
        if root.tag.split("}")[-1] != "gpx":
            raise ValueError("Expected a GPX document")
        groups = {name: [] for name in ("trkpt", "rtept", "wpt")}
        for element in root.iter():
            tag = element.tag.split("}")[-1]
            if tag in groups:
                groups[tag].append(
                    Coordinates(latitude=element.attrib["lat"], longitude=element.attrib["lon"])
                )
        points = groups["trkpt"] or groups["rtept"] or groups["wpt"]
        if not 2 <= len(points) <= 10000:
            raise ValueError("GPX requires 2–10,000 points")
        return points
    except Exception as exc:
        raise ValueError("Invalid GPX: " + str(exc)) from exc
