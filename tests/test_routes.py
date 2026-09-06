import pytest

from models.schemas import Coordinates
from services.movement_engine import destination, distance
from services.route_engine import RouteEngine


@pytest.fixture
def points():
    a = Coordinates(latitude=13.7563, longitude=100.5018)
    return [a, destination(a, 90, 10), destination(a, 90, 20)]


def test_progress_and_completion(points):
    route = RouteEngine(points)
    p, _ = route.advance(points[0], 5)
    assert distance(points[0], p) == pytest.approx(5, abs=1e-6)
    assert route.snapshot()["route_progress"] == pytest.approx(0.25)
    p, _ = route.advance(p, 100)
    assert p == points[-1]
    assert route.status == "completed"
    assert route.snapshot()["distance_remaining"] == 0


def test_pause_resume(points):
    route = RouteEngine(points)
    route.status = "paused"
    assert route.advance(points[0], 100)[0] == points[0]
    assert route.travelled == 0
    route.status = "running"
    assert route.advance(points[0], 100)[0] == points[-1]


def test_loop_returns_continuously(points):
    route = RouteEngine(points, 2)
    p, _ = route.advance(points[0], 25)
    assert distance(points[0], p) == pytest.approx(15, abs=1e-6)
    assert route.completed_loops == 1
    assert route.status == "running"
    p, _ = route.advance(p, 40)
    assert p == points[-1]
    assert route.completed_loops == 2
    assert route.status == "completed"
    assert route.travelled == pytest.approx(60, abs=1e-6)


def test_infinite_loop_and_duplicates(points):
    route = RouteEngine([points[0], points[0], points[1]], 0)
    route.advance(points[0], 1000)
    assert route.status == "running"
    assert route.completed_loops >= 49
    assert route.snapshot()["distance_remaining"] is None


def test_invalid_route(points):
    with pytest.raises(ValueError):
        RouteEngine([points[0], points[0]])
    with pytest.raises(ValueError):
        RouteEngine([points[0]])
