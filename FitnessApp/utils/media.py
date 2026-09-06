# Shared media-URL helpers. Lives outside any single app (accounts /
# workouts both need it) specifically to avoid a circular import: accounts/
# functions.py already imports from accounts/serializers.py, so a serializer
# module can't import a helper defined in accounts/functions.py without a
# cycle.

from decouple import config

DEFAULT_GYM_ICON_URL = config(
    "DEFAULT_GYM_ICON_URL",
    default="https://res.cloudinary.com/dzxtx8e4q/image/upload/v1775587332/gym_icon_ijfhb3.png",
)
DEFAULT_PROFILE_ICON_URL = config(
    "DEFAULT_PROFILE_ICON_URL",
    default="https://res.cloudinary.com/dzxtx8e4q/image/upload/v1774515327/profile_icon_zgwn3s.png",
)


def thumbnail_url(url, size=150, width=None, height=None):
    """
    Insert a Cloudinary sizing/format transformation into an /upload/ URL so a
    list of small thumbnails (gym icons, profile avatars, gym photo cards...)
    doesn't make each row download the full-resolution original — serving the
    full image for a small display size is what makes a list feel slow to
    render. `size` is a convenience for square avatars/icons (width=height);
    pass `width`/`height` separately for a non-square crop (e.g. a landscape
    card photo).
    """
    if not url or "/upload/" not in url:
        return url
    w = width or size
    h = height or size
    marker = "/upload/"
    idx = url.index(marker) + len(marker)
    transform = f"w_{w},h_{h},c_fill,q_auto,f_auto/"
    return url[:idx] + transform + url[idx:]
