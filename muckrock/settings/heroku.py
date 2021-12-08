"""
Settings used when deployed on heroku
Not used directly - imported from production and staging settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

INSTALLED_APPS = ("scout_apm.django",) + INSTALLED_APPS
USE_SCOUT = True

TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]
del TEMPLATES[0]["APP_DIRS"]

if "MEMCACHIER_SERVERS" in os.environ:
    servers = os.environ.get("MEMCACHIER_SERVERS", "")
    username = os.environ.get("MEMCACHIER_USERNAME", "")
    password = os.environ.get("MEMCACHIER_PASSWORD", "")

    CACHES["default"] = {
        # Use pylibmc
        "BACKEND": "django_bmemcached.memcached.BMemcached",
        # TIMEOUT is not the connection timeout! It's the default expiration
        # timeout that should be applied to keys! Setting it to `None`
        # disables expiration.
        "TIMEOUT": None,
        "LOCATION": servers,
        "OPTIONS": {"username": username, "password": password},
    }

CONSTANCE_DATABASE_CACHE_BACKEND = "default"
