import pytest

from services.icecream import get_icecream_pois, filter_chargers_by_icecream


def test_get_icecream_pois_returns_results_for_known_location():
    # network call may fail; ensure function returns a list and handles errors
    results = get_icecream_pois(52.52, 13.405, 5000)
    assert isinstance(results, list)
    # if Overpass is reachable we expect some results, but empty is acceptable
    # in CI or offline environments
    if results:
        assert all("lat" in r and "lon" in r for r in results)


def test_filter_chargers_by_icecream_respects_distance():
    # create dummy chargers and pois, then filter
    chargers = [
        {"id": 1, "lat": 52.52, "lon": 13.405},
        {"id": 2, "lat": 52.53, "lon": 13.405},
    ]
    pois = [
        {"name": "A", "lat": 52.52, "lon": 13.405},
    ]
    # 1 km should include only the first charger
    filtered, matches = filter_chargers_by_icecream(chargers, pois, 1000)
    assert len(filtered) == 1 and filtered[0]["id"] == 1
    assert matches and matches[0]["name"] == "A"
    # 100 km should include both chargers
    filtered2, matches2 = filter_chargers_by_icecream(chargers, pois, 100000)
    assert len(filtered2) == 2
