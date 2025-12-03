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
        self.last_update_success_time: datetime | None = None

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
            try:
                zone_data[zone_name] = await self._calculate_zone_times(zone_name)
            except Exception as err:  # pylint: disable=broad-except
                LOGGER.error("Error calculating time for zone %s: %s", zone_name, err)
                # Return 0 values on error to keep sensor available
                zone_data[zone_name] = {
                    PERIOD_TODAY: 0.0,
                    PERIOD_WEEK: 0.0,
                    PERIOD_MONTH: 0.0,
                }

        self.last_update_success_time = dt_util.now()
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
            history.get_significant_states,
            self.hass,
            start_time,
            end_time,
            [self._person_entity],
            None,
            True,  # include_start_time_state
            True,  # significant_changes_only
        )

        if not states:
            LOGGER.info("No history states found for %s", self._person_entity)
            return 0.0
            
        if self._person_entity not in states:
            LOGGER.info("Person entity %s not in history states", self._person_entity)
            return 0.0

        person_states = states[self._person_entity]
        if not person_states:
            LOGGER.info("Empty state list for %s", self._person_entity)
            return 0.0
            
        LOGGER.info(
            "Found %d states for %s between %s and %s (zone=%s)", 
            len(person_states), 
            self._person_entity,
            start_time,
            end_time,
            zone_entity_id
        )

        # Get the zone's friendly name from the zone entity
        # Person entities use the zone's friendly name, not the entity_id
        zone_state = self.hass.states.get(zone_entity_id)
        if zone_state is None:
            LOGGER.warning("Zone entity %s not found", zone_entity_id)
            return 0.0
            
        # The zone's friendly name is in the attributes
        target_zone = zone_state.attributes.get("friendly_name", zone_entity_id.replace("zone.", ""))
        
        # Log first few states to see what we're working with
        if len(person_states) > 0:
            sample_states = [s.state for s in person_states[:5]]
            LOGGER.info(
                "Target zone: '%s' (from %s), Sample person states: %s",
                target_zone,
                zone_entity_id,
                sample_states
            )

        total_seconds = 0.0
        last_zone_entry = None

        for i, state in enumerate(person_states):
            current_state = state.state
            current_time = state.last_updated
            
            # Ensure we don't count time before the start_time
            if current_time < start_time:
                current_time = start_time

            # Check if person is in the target zone
            if current_state == target_zone:
                if last_zone_entry is None:
                    # Entering zone
                    last_zone_entry = current_time
            else:
                # Not in zone anymore or different zone
                if last_zone_entry is not None:
                    # Calculate duration
                    # Ensure we don't count time after end_time (though unlikely with history)
                    if current_time > end_time:
                        current_time = end_time
                        
                    duration = (current_time - last_zone_entry).total_seconds()
                    total_seconds += duration
                    last_zone_entry = None

        # If still in zone at end time, count duration until end
        if last_zone_entry is not None:
            duration = (end_time - last_zone_entry).total_seconds()
            total_seconds += duration

        # Convert seconds to hours
        hours = round(total_seconds / 3600, 2)
        LOGGER.info(
            "Calculated %.2f hours for %s in zone %s (period: %s to %s)",
            hours,
            self._person_entity,
            zone_entity_id,
            start_time,
            end_time
        )
        return hours

    def _get_week_start(self, dt: datetime) -> datetime:
        """Get the start of the week (Monday at 00:00)."""
        days_since_monday = dt.weekday()
        week_start = dt - timedelta(days=days_since_monday)
        return dt_util.start_of_local_day(week_start)
