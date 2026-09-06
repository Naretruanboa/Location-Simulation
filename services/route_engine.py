from models.schemas import Coordinates
from services.movement_engine import bearing, destination, distance


class RouteEngine:
    """Repeated routes return along a geodesic closing segment; never jump to the start."""

    def __init__(self, points: list[Coordinates], loops: int = 1):
        if len(points) < 2 or sum(distance(a, b) for a, b in zip(points, points[1:])) < 0.01:
            raise ValueError("Route must contain at least two distinct points")
        self.points = points
        self.loops = loops
        self.current_segment = 0
        self.completed_loops = 0
        self.status = "running"
        self.travelled = 0.0
        self.base_distance = sum(distance(a, b) for a, b in zip(points, points[1:]))
        self.closing_distance = distance(points[-1], points[0])

    def advance(self, position: Coordinates, meters: float) -> tuple[Coordinates, float]:
        heading = 0.0
        if self.status != "running":
            return position, heading
        while meters > 0 and self.status == "running":
            target = self.points[(self.current_segment + 1) % len(self.points)]
            remaining = distance(position, target)
            heading = bearing(position, target)
            step = min(meters, remaining)
            self.travelled += step
            meters -= step
            if remaining > step + 1e-8:
                return destination(position, heading, step), heading
            position = target
            self.current_segment += 1
            if self.current_segment == len(self.points) - 1:
                self.completed_loops += 1
                if self.loops and self.completed_loops >= self.loops:
                    self.status = "completed"
            elif self.current_segment == len(self.points):
                self.current_segment = 0
        return position, heading

    def snapshot(self) -> dict:
        total = self.base_distance * self.loops + self.closing_distance * max(0, self.loops - 1)
        return {
            "type": "route_state",
            "status": self.status,
            "current_segment": self.current_segment,
            "completed_loops": self.completed_loops,
            "loops": self.loops,
            "route_progress": (1.0 if self.status == "completed" else min(1, self.travelled / total))
            if total
            else None,
            "distance_remaining": (0.0 if self.status == "completed" else max(0, total - self.travelled))
            if self.loops
            else None,
        }
