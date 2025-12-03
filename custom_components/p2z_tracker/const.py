"""Constants for p2z_tracker."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "p2z_tracker"

# Configuration keys
CONF_PERSON_ENTITY = "person_entity"
CONF_TRACKED_ZONES = "tracked_zones"
CONF_ZONE_NAME = "zone_name"
CONF_DISPLAY_NAME = "display_name"
CONF_ENABLE_BACKFILL = "enable_backfill"
CONF_BACKFILL_DAYS = "backfill_days"
CONF_RETENTION_DAYS = "retention_days"
CONF_ENABLE_AVERAGES = "enable_averages"

# Time periods
PERIOD_TODAY = "today"
PERIOD_WEEK = "week"
PERIOD_MONTH = "month"

# Sensor attributes
ATTR_ZONE_NAME = "zone_name"
ATTR_PERSON_ENTITY = "person_entity"
ATTR_PERIOD = "period"
ATTR_LAST_UPDATED = "last_updated"
ATTR_BACKFILLED = "backfilled"

# Default values
DEFAULT_RETENTION_DAYS = 90
DEFAULT_UPDATE_INTERVAL = 60  # seconds
