import pytest

from services import icecream
from services.icecream import get_icecream_pois


def test_retry_and_fallback(monkeypatch):
    # clear caching so each call executes logic
    try:
        get_icecream_pois.cache_clear()
    except AttributeError:
        pass

    class DummyResp:
        def __init__(self, status, json_data=None, text=""):
            self.status_code = status
            self._json = json_data or {"elements": []}
            self.text = text

        def json(self):
            return self._json

    calls = []

    def fake_post(url, data, timeout):
        calls.append(url)
        if url == icecream.PRIMARY_OVERPASS_URL:
            if len(calls) == 1:
                return DummyResp(504, text="timeout")
            return DummyResp(200, {"elements": []})
        return DummyResp(200, {"elements": []})

    monkeypatch.setattr(icecream.requests, "post", fake_post)
    result = get_icecream_pois(1, 2, 3)
    assert result == []
    assert calls[0] == icecream.PRIMARY_OVERPASS_URL
    assert len(calls) >= 2

    # simulate primary failure so fallback is used
    try:
        get_icecream_pois.cache_clear()
    except AttributeError:
        pass
    calls.clear()

    def fake_post_fail(url, data, timeout):
        calls.append(url)
        if url == icecream.PRIMARY_OVERPASS_URL:
            return DummyResp(500, text="bad")
        return DummyResp(200, {"elements": []})

    monkeypatch.setattr(icecream.requests, "post", fake_post_fail)
    result2 = get_icecream_pois(4, 5, 6)
    assert result2 == []
    assert calls[0] == icecream.PRIMARY_OVERPASS_URL
    assert calls[1] == icecream.FALLBACK_OVERPASS_URL
