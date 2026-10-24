"""Live data: weather from Open-Meteo (no key) and mandi prices from Agmarknet via data.gov.in (free key)."""
import datetime as dt, os, statistics, time
import requests
from common import CROPS, REGIONS

_cache = {}


def _cached(key, ttl, fn):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    val = fn()
    _cache[key] = (time.time(), val)
    return val


def season_weather(region, season, year):
    """Mean temperature, total rainfall and mean humidity for the most recent finished season,
    used as a planning estimate for the coming one."""
    _, lat, lon = REGIONS[region]
    if season == "Kharif":
        start, end = dt.date(year - 1, 6, 1), dt.date(year - 1, 9, 30)
    else:
        start, end = dt.date(year - 1, 10, 1), dt.date(year, 2, 28)
    today = dt.date.today() - dt.timedelta(days=7)      # archive lags a few days
    if end > today:                                     # season not finished: use the year before
        start, end = start.replace(year=start.year - 1), end.replace(year=end.year - 1)

    def fetch():
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=15, params=dict(
            latitude=lat, longitude=lon, start_date=start.isoformat(), end_date=end.isoformat(),
            daily="temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean", timezone="auto"))
        r.raise_for_status()
        d = r.json()["daily"]
        t = [x for x in d["temperature_2m_mean"] if x is not None]
        p = [x for x in d["precipitation_sum"] if x is not None]
        h = [x for x in d["relative_humidity_2m_mean"] if x is not None]
        return dict(temp=round(sum(t) / len(t), 1), rain=round(sum(p)), hum=round(sum(h) / len(h)),
                    period=f"{start} to {end}", source="Open-Meteo historical archive")
    return _cached(("w", region, season, start), 6 * 3600, fetch)


def mandi_price(crop, region):
    """Median modal price in Rs/kg across recent market arrivals, or None if unavailable."""
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        return None
    rid = os.environ.get("MANDI_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070")

    def fetch():
        r = requests.get(f"https://api.data.gov.in/resource/{rid}", timeout=15, params={
            "api-key": key, "format": "json", "limit": 100,
            "filters[state]": region, "filters[commodity]": CROPS[crop]["mandi"]})
        r.raise_for_status()
        vals = []
        for rec in r.json().get("records", []):
            try:
                vals.append(float(rec["modal_price"]) / 100)    # Rs/quintal -> Rs/kg
            except (KeyError, ValueError, TypeError):
                pass
        if not vals:
            return None
        return dict(price=round(statistics.median(vals), 2), n=len(vals), source="Agmarknet (data.gov.in)")
    try:
        return _cached(("p", crop, region), 6 * 3600, fetch)
    except requests.RequestException:
        return None
