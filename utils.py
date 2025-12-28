import os
import time
from datetime import datetime
from threading import Lock
from urllib.parse import urlencode

import requests

DEFAULT_USER_AGENT = "(weather.jawand.dev, jawandsingh@gmail.com)"

# In-memory cache for API rate limiting (not persisted to disk)
_MEMORY_CACHE = {"meta": {}, "groups": {}, "aliases": {}}
CACHE_LOCK = Lock()


def get_weather_headers():
    user_agent = os.getenv("WEATHER_GOV_USER_AGENT", DEFAULT_USER_AGENT)
    return {
        "User-Agent": user_agent,
        "Accept": "application/geo+json",
    }


def get_geocoder_headers():
    user_agent = os.getenv("WEATHER_GOV_USER_AGENT", DEFAULT_USER_AGENT)
    return {
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Accept-Language": "en",
    }


def format_location_key(city, state):
    """Create a canonical location key from City, State."""
    if not city or not state:
        return None
    # Normalize to "City, State" format
    city = city.strip()
    state = state.strip()
    return f"{city}, {state}"


def format_coordinate_alias(lat_value, lon_value):
    """Create an alias key from lat/lon coordinates."""
    try:
        lat = float(lat_value)
        lon = float(lon_value)
    except (TypeError, ValueError):
        return None
    return f"coord:{lat:.4f},{lon:.4f}"


def resolve_location_alias(alias_key):
    """Resolve an alias (coordinates, zip, etc.) to canonical City, State location key."""
    if not alias_key:
        return None
    with CACHE_LOCK:
        _ensure_today()
        aliases = _MEMORY_CACHE.get("aliases", {})
        return aliases.get(alias_key)


def register_location_alias(alias_key, canonical_key):
    """Register an alias (coordinates, zip, etc.) to point to canonical City, State location."""
    if not alias_key or not canonical_key:
        return
    with CACHE_LOCK:
        _ensure_today()
        if "aliases" not in _MEMORY_CACHE:
            _MEMORY_CACHE["aliases"] = {}
        _MEMORY_CACHE["aliases"][alias_key] = canonical_key


def location_group_key(location_key):
    if not location_key:
        return "default"
    return f"loc:{location_key}"


def _cache_key(url, params):
    if not params:
        return url
    query = urlencode(sorted(params.items(), key=lambda item: item[0]), doseq=True)
    return f"{url}?{query}"


def _today_key():
    return datetime.now().date().isoformat()


def _ensure_today():
    """Reset in-memory cache if the day has changed."""
    today = _today_key()
    if _MEMORY_CACHE.get("meta", {}).get("last_refresh_date") != today:
        _MEMORY_CACHE["groups"] = {}
        _MEMORY_CACHE["aliases"] = {}
        _MEMORY_CACHE["meta"] = {"last_refresh_date": today}
        return True
    return False


def _prune_group_cache(group_cache, now):
    for key in list(group_cache.keys()):
        entry = group_cache.get(key, {})
        if entry.get("expires_at", 0) <= now:
            group_cache.pop(key, None)


def cached_get_json(
    url, *, headers=None, params=None, timeout=10, ttl=600, cache_group="default"
):
    """
    Fetch JSON with in-memory caching for API rate limiting.
    Cache is not persisted to disk - it only lasts for the server session.
    """
    cache_key = _cache_key(url, params)
    now = time.time()
    with CACHE_LOCK:
        _ensure_today()
        group_cache = _MEMORY_CACHE.get("groups", {}).get(cache_group, {})
        cached = group_cache.get(cache_key)
        if cached and cached.get("expires_at", 0) > now:
            return cached.get("value")

    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    with CACHE_LOCK:
        _ensure_today()
        group_cache = _MEMORY_CACHE.setdefault("groups", {}).setdefault(cache_group, {})
        write_time = time.time()
        _prune_group_cache(group_cache, write_time)
        group_cache[cache_key] = {"expires_at": write_time + ttl, "value": data}
    return data


def clear_cache():
    """Clear all in-memory cache."""
    with CACHE_LOCK:
        _MEMORY_CACHE["groups"] = {}
        _MEMORY_CACHE["aliases"] = {}
        _MEMORY_CACHE["meta"] = {"last_refresh_date": _today_key()}


def clear_cache_group(cache_group):
    """Clear a specific cache group."""
    if not cache_group:
        return
    with CACHE_LOCK:
        _ensure_today()
        _MEMORY_CACHE.get("groups", {}).pop(cache_group, None)


def clear_location_cache(location_key):
    """Clear cache for a specific location."""
    if not location_key:
        return
    clear_cache_group(location_group_key(location_key))


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_hour_label(dt):
    if not dt:
        return None
    return dt.strftime("%I %p").lstrip("0")


def format_alert_time(value):
    dt = parse_iso_datetime(value)
    if not dt:
        return None
    return dt.strftime("%a %I:%M %p").lstrip("0")
