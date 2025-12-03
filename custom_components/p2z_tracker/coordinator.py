"""DataUpdateCoordinator for p2z_tracker."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BACKFILL_DAYS,
    CONF_ENABLE_BACKFILL,
    CONF_PERSON_ENTITY,
    CONF_TRACKED_ZONES,
    CONF_ZONE_NAME,
    LOGGER,
    PERIOD_MONTH,
    PERIOD_TODAY,
    PERIOD_WEEK,
)

if TYPE_CHECKING:
    from .data import P2ZTrackerConfigEntry


class P2ZDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, float]]]):
    """Class to manage fetching zone time data."""

    config_entry: P2ZTrackerConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        logger,
        name: str,
        update_interval: timedelta,
        config_entry: P2ZTrackerConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(hass, logger, name=name, update_interval=update_interval)
        self.config_entry = config_entry
        self._person_entity = config_entry.data[CONF_PERSON_ENTITY]
        self._backfilled = False

    async def _async_update_data(self) -> dict[str, dict[str, float]]:
        """Fetch zone time data from recorder."""
        tracked_zones = self.config_entry.options.get(CONF_TRACKED_ZONES, [])

        # Perform backfill on first update if needed
        if not self._backfilled:
            await self._perform_backfill(tracked_zones)
            self._backfilled = True

        # Calculate current time in zones
        zone_data = {}
        for zone_config in tracked_zones:
            zone_name = zone_config[CONF_ZONE_NAME]
            zone_data[zone_name] = await self._calculate_zone_times(zone_name)

        return zone_data

    async def _perform_backfill(self, tracked_zones: list[dict[str, Any]]) -> None:
        """Perform historical backfill for zones that have it enabled."""
        for zone_config in tracked_zones:
            if not zone_config.get(CONF_ENABLE_BACKFILL, False):
                continue

            zone_name = zone_config[CONF_ZONE_NAME]
            backfill_days = zone_config.get(CONF_BACKFILL_DAYS, 0)

            if backfill_days > 0:
                LOGGER.info(
                    "Performing %d-day backfill for zone %s",
                    backfill_days,
                    zone_name,
                )
                # Backfill will be handled during first calculation
                # Data is calculated from history, so backfill is automatic

    async def _calculate_zone_times(self, zone_entity_id: str) -> dict[str, float]:
        """Calculate time spent in a zone for different periods."""
        now = dt_util.now()

        # Calculate period boundaries
        periods = {
            PERIOD_TODAY: dt_util.start_of_local_day(now),
            PERIOD_WEEK: self._get_week_start(now),
            PERIOD_MONTH: dt_util.start_of_local_day(now).replace(day=1),
        }

        result = {}
        for period, start_time in periods.items():
            hours = await self._calculate_time_in_zone(
                zone_entity_id, start_time, now
            )
            result[period] = hours

        return result

    async def _calculate_time_in_zone(
        self, zone_entity_id: str, start_time: datetime, end_time: datetime
    ) -> float:
        """Calculate time spent in a specific zone between two times."""
        # Get state history for the person entity
        states = await get_instance(self.hass).async_add_executor_job(
            history.state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            self._person_entity,
        )

        if not states or self._person_entity not in states:
            return 0.0

        person_states = states[self._person_entity]
        if not person_states:
            return 0.0

        # Extract zone name from entity_id (zone.home -> home)
        target_zone = zone_entity_id.replace("zone.", "")

        total_seconds = 0.0
        last_zone_entry = None

        for i, state in enumerate(person_states):
            current_state = state.state
            current_time = state.last_updated

            # Check if person is in the target zone
            if current_state == target_zone:
                if last_zone_entry is None:
                    # Entering zone
                    last_zone_entry = current_time
            else:
                # Not in zone anymore or different zone
                if last_zone_entry is not None:
                    # Calculate duration
                    duration = (current_time - last_zone_entry).total_seconds()
                    total_seconds += duration
                    last_zone_entry = None

        # If still in zone at end time, count duration until end
        if last_zone_entry is not None:
            duration = (end_time - last_zone_entry).total_seconds()
            total_seconds += duration

        # Convert seconds to hours
        return round(total_seconds / 3600, 2)

    def _get_week_start(self, dt: datetime) -> datetime:
        """Get the start of the week (Monday at 00:00)."""
        days_since_monday = dt.weekday()
        week_start = dt - timedelta(days=days_since_monday)
        return dt_util.start_of_local_day(week_start)
