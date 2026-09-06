"""
Small read-through cache for data that changes rarely (plan tiers, plans,
lookup lists) but is fetched on nearly every app launch. Uses Django's
default cache backend (LocMemCache — per-process, no extra infra). A short
TTL bounds staleness; model signals bust the keys immediately on admin edits.
"""
from django.core.cache import cache

# --- keys ---------------------------------------------------------------
PLAN_SCREEN_KEY = "cache:plan_screen"          # merged tiers + plans
PLAN_TIERS_KEY = "cache:plan_tiers"
PLAN_LIST_KEY = "cache:plan_list:{code}"       # {code} = premim_type or "all"
WORKOUT_TYPES_KEY = "cache:workout_types"
GYM_FEATURES_KEY = "cache:gym_features"

# --- TTLs (seconds) ---------------------------------------------------
PLAN_TTL = 60 * 10       # 10 min
LOOKUP_TTL = 60 * 30     # 30 min

_PREMIUM_CODES = ("all", "B", "V", "E")


def get_or_set(key, builder, ttl):
    """cache.get_or_set with a clearer name; builder() is a zero-arg callable."""
    return cache.get_or_set(key, builder, ttl)


def invalidate_plans():
    cache.delete(PLAN_SCREEN_KEY)
    cache.delete(PLAN_TIERS_KEY)
    cache.delete_many([PLAN_LIST_KEY.format(code=c) for c in _PREMIUM_CODES])


def invalidate_workout_types():
    cache.delete(WORKOUT_TYPES_KEY)


def invalidate_gym_features():
    cache.delete(GYM_FEATURES_KEY)
