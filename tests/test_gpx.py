import pytest

from services.gpx_parser import parse_gpx


@pytest.mark.parametrize("tag", ["trkpt", "rtept", "wpt"])
def test_valid_gpx(tag):
    points = parse_gpx(
        f'<gpx xmlns="http://www.topografix.com/GPX/1/1"><{tag} lat="13" lon="100"/><{tag} lat="14" lon="101"/></gpx>'
    )
    assert len(points) == 2
    assert points[1].longitude == 101


@pytest.mark.parametrize(
    "xml",
    [
        "no xml",
        "<gpx/>",
        '<gpx><wpt lat="91" lon="0"/></gpx>',
        "<gpx><wpt/></gpx>",
        "<wrong/>",
        '<!DOCTYPE x [<!ENTITY x "boom">]><gpx>&x;</gpx>',
    ],
)
def test_bad_gpx(xml):
    with pytest.raises(ValueError):
        parse_gpx(xml)


def test_track_precedence():
    xml = '<gpx><wpt lat="1" lon="1"/><trk><trkseg><trkpt lat="2" lon="2"/><trkpt lat="3" lon="3"/></trkseg></trk></gpx>'
    assert parse_gpx(xml)[0].latitude == 2
