"""Constants for SolarEdge Home Automation."""

from __future__ import annotations

from logging import Logger, getLogger

DOMAIN = "solaredge_home_automation"
LOGGER: Logger = getLogger(__package__)

CONF_SITE_ID = "site_id"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL_MINUTES = 15
MIN_SCAN_INTERVAL_MINUTES = 1
MAX_SCAN_INTERVAL_MINUTES = 60

DATA_COORDINATOR = "coordinator"

EV_CHARGER = "EV_CHARGER"
SMART_DEVICE_TYPES = {"ON_OFF"}

DEFAULT_TIMER_DURATION_MINUTES = 5
MIN_TIMER_DURATION_MINUTES = 1
MAX_TIMER_DURATION_MINUTES = 1440
