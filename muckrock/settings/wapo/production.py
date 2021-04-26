"""
Washington Post setting overrides for production
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from mucrock.settings.production import *

# TODO Remove me once we've verified email sending in production
EMAIL_BACKEND = "muckrock.settings.staging.HijackMailgunBackend"
BANDIT_EMAIL = os.environ.get("BANDIT_EMAIL", "staging@muckrock.com")
BANDIT_WHITELIST = [
    e.strip() for e in os.environ.get("BANDIT_WHITELIST", "").split(",") if e.strip()
]

# This gets the IP address of the EC2 instance the task is
# running on and adds it to allowed_hosts so the health
# check will work
try:
    EC2_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4').text
    ALLOWED_HOSTS.append(EC2_IP)
except requests.exceptions.RequestException:
    pass