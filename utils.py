import json
import os
import time
from datetime import datetime
from threading import Lock
from urllib.parse import urlencode

import requests

DEFAULT_USER_AGENT = "(weather.jawand.dev, jawandsingh@gmail.com)"
CACHE_FILE = os.getenv("WEATHER_CACHE_FILE", "/data/weather_cache.json")
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


def format_location_key(lat_value, lon_value):
    try:
        lat = float(lat_value)
        lon = float(lon_value)
    except (TypeError, ValueError):
        return None
    return f"{lat:.4f},{lon:.4f}"


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


def _empty_cache():
    return {"meta": {"last_refresh_date": _today_key()}, "groups": {}, "locations": {}}


def _normalize_cache(raw_cache):
    if not isinstance(raw_cache, dict):
        return _empty_cache()
    if "groups" not in raw_cache:
        raw_cache = {"meta": {}, "groups": {"default": raw_cache}, "locations": {}}
    raw_cache.setdefault("meta", {})
    raw_cache.setdefault("locations", {})
    raw_cache.setdefault("groups", {})
    if not isinstance(raw_cache.get("groups"), dict):
        raw_cache["groups"] = {}
    if not isinstance(raw_cache.get("locations"), dict):
        raw_cache["locations"] = {}
    return raw_cache


def _ensure_today(cache):
    today = _today_key()
    if cache.get("meta", {}).get("last_refresh_date") != today:
        cache["groups"] = {}
        cache["locations"] = {}
        cache["meta"]["last_refresh_date"] = today
        return True
    return False


def _load_cache_file():
    if not os.path.exists(CACHE_FILE):
        return _empty_cache()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return _normalize_cache(data)
    except (OSError, json.JSONDecodeError):
        return _empty_cache()


def _write_cache_file(cache):
    cache_dir = os.path.dirname(CACHE_FILE)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    temp_path = f"{CACHE_FILE}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(cache, handle)
        os.replace(temp_path, CACHE_FILE)
    except OSError:
        return


def _prune_group_cache(group_cache, now):
    for key in list(group_cache.keys()):
        entry = group_cache.get(key, {})
        if entry.get("expires_at", 0) <= now:
            group_cache.pop(key, None)


def cached_get_json(
    url, *, headers=None, params=None, timeout=10, ttl=600, cache_group="default"
):
    cache_key = _cache_key(url, params)
    now = time.time()
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        group_cache = cache.get("groups", {}).get(cache_group, {})
        cached = group_cache.get(cache_key)
        if cached and cached.get("expires_at", 0) > now:
            return cached.get("value")

    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        group_cache = cache.get("groups", {}).setdefault(cache_group, {})
        write_time = time.time()
        _prune_group_cache(group_cache, write_time)
        group_cache[cache_key] = {"expires_at": write_time + ttl, "value": data}
        cache["groups"][cache_group] = group_cache
        _write_cache_file(cache)
    return data


def clear_cache():
    with CACHE_LOCK:
        for path in (CACHE_FILE, f"{CACHE_FILE}.tmp"):
            try:
                os.remove(path)
            except FileNotFoundError:
                continue
            except OSError:
                continue


def register_location(location_key, label, lat, lon):
    if not location_key:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        cache["locations"][location_key] = {
            "label": label or location_key,
            "lat": float(lat),
            "lon": float(lon),
            "updated_at": int(time.time()),
        }
        _write_cache_file(cache)


def list_cached_locations():
    with CACHE_LOCK:
        cache = _load_cache_file()
        changed = _ensure_today(cache)
        locations = []
        for key, value in cache.get("locations", {}).items():
            if not isinstance(value, dict):
                continue
            label = str(value.get("label") or key)
            locations.append(
                {
                    "key": key,
                    "label": label,
                    "lat": value.get("lat"),
                    "lon": value.get("lon"),
                }
            )
        if changed:
            _write_cache_file(cache)
    return sorted(locations, key=lambda item: item["label"].lower())


def clear_cache_group(cache_group):
    if not cache_group:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        cache.get("groups", {}).pop(cache_group, None)
        _write_cache_file(cache)


def clear_location_cache(location_key):
    if not location_key:
        return
    clear_cache_group(location_group_key(location_key))


def delete_location_cache(location_key):
    if not location_key:
        return
    with CACHE_LOCK:
        cache = _load_cache_file()
        _ensure_today(cache)
        cache.get("groups", {}).pop(location_group_key(location_key), None)
        cache.get("locations", {}).pop(location_key, None)
        _write_cache_file(cache)


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
