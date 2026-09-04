# Per-tier copy for the Plan page (mobile app ChoosePlan screen).
#
# The tab list itself is derived at runtime from the active SubscriptionPlan
# rows (their `premim_type`), so this file only holds the text/flags that have
# nowhere else to live. Keyed by premim_type code ('B' / 'V' / 'E').
# Editing here takes effect on the next deploy — no migration, no DB row.

TIER_COPY = {
    "B": {
        "description": "With the Basic Plan, you can access partner gyms included in the Basic plans.",
        "show_gym_link": True,
        "gym_link_label": "Available gyms",
        "gym_link_url": "/gyms?plan-type=B",
    },
    "V": {
        "description": "With the VIP Plan, you can access partner gyms included in the <b>Basic</b> and <b>VIP</b> plans.",
        "show_gym_link": False,
        "gym_link_label": "Available gyms",
        "gym_link_url": "/gyms?plan-type=V",
    },
    "E": {
        "description": "With the Elite Plan, you can access all partner gyms available on the Fitzz platform.",
        "show_gym_link": False,
        "gym_link_label": "Available gyms",
        "gym_link_url": "/gyms?plan-type=E",
    },
}

DEFAULT_TIER_COPY = {
    "description": "",
    "show_gym_link": False,
    "gym_link_label": "Available gyms",
    "gym_link_url": "",
}


def tier_copy(code):
    return {**DEFAULT_TIER_COPY, **TIER_COPY.get(code, {})}
