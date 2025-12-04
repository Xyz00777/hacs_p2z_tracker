"""Sensor platform for p2z_tracker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    ATTR_BACKFILLED,
    ATTR_LAST_UPDATED,
    ATTR_PERIOD,
    ATTR_PERSON_ENTITY,
    ATTR_ZONE_NAME,
    CONF_DISPLAY_NAME,
    CONF_ENABLE_AVERAGES,
    CONF_ENABLE_BACKFILL,
    CONF_PERSON_ENTITY,
    CONF_TRACKED_ZONES,
    CONF_ZONE_NAME,
    DOMAIN,
    PERIOD_MONTH,
    PERIOD_TODAY,
    PERIOD_WEEK,
    PERIOD_MONDAY,
    PERIOD_TUESDAY,
    PERIOD_WEDNESDAY,
    PERIOD_THURSDAY,
    PERIOD_FRIDAY,
    PERIOD_SATURDAY,
    PERIOD_SUNDAY,
)
from .coordinator import P2ZDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import P2ZTrackerConfigEntry


PERIODS = [PERIOD_TODAY, PERIOD_WEEK, PERIOD_MONTH]
WEEKDAY_PERIODS = [
    PERIOD_MONDAY,
    PERIOD_TUESDAY,
    PERIOD_WEDNESDAY,
    PERIOD_THURSDAY,
    PERIOD_FRIDAY,
    PERIOD_SATURDAY,
    PERIOD_SUNDAY,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: P2ZTrackerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    person_entity = entry.data[CONF_PERSON_ENTITY]
    tracked_zones = entry.options.get(CONF_TRACKED_ZONES, [])

    from .const import LOGGER
    LOGGER.info(
        "Setting up sensors for person %s with %d tracked zones",
        person_entity,
        len(tracked_zones),
    )

    # Create sensors for each tracked zone
    sensors = []
    for zone_config in tracked_zones:
        zone_name = zone_config[CONF_ZONE_NAME]
        display_name = zone_config.get(CONF_DISPLAY_NAME)
        if not display_name:
            display_name = zone_name
        backfilled = zone_config.get(CONF_ENABLE_BACKFILL, False)
        enable_averages = zone_config.get(CONF_ENABLE_AVERAGES, False)

        LOGGER.debug("Creating sensors for zone: %s", zone_name)

        # Create standard sensors (today, week, month)
        for period in PERIODS:
            sensors.append(
                ZoneTimeSensor(
                    coordinator=coordinator,
                    person_entity=person_entity,
                    zone_entity_id=zone_name,
                    display_name=display_name,
                    period=period,
                    backfilled=backfilled,
                    is_average=False,
                )
            )
        
        # Create average sensors if enabled
        if enable_averages:
            for period in WEEKDAY_PERIODS:
                sensors.append(
                    ZoneTimeSensor(
                        coordinator=coordinator,
                        person_entity=person_entity,
                        zone_entity_id=zone_name,
                        display_name=display_name,
                        period=period,
                        backfilled=backfilled,
                        is_average=True,
                    )
                )

    LOGGER.info("Adding %d sensors to Home Assistant", len(sensors))
    async_add_entities(sensors)


class ZoneTimeSensor(CoordinatorEntity[P2ZDataUpdateCoordinator], SensorEntity):
    """Sensor tracking time spent in a zone."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(
        self,
        coordinator: P2ZDataUpdateCoordinator,
        person_entity: str,
        zone_entity_id: str,
        display_name: str,
        period: str,
        backfilled: bool,
        is_average: bool = False,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._person_entity = person_entity
        self._zone_entity_id = zone_entity_id
        self._display_name = display_name
        self._period = period
        self._backfilled = backfilled
        self._is_average = is_average

        # Generate entity ID
        person_name = person_entity.replace("person.", "")
        zone_slug = slugify(zone_entity_id.replace("zone.", ""))
        avg_suffix = "_avg" if is_average else ""
        self._attr_unique_id = f"p2z_{person_name}_{zone_slug}_{period}{avg_suffix}"
        self.entity_id = f"sensor.p2z_{person_name}_{zone_slug}_{period}{avg_suffix}"

        # Format period name for display
        period_name = self._period.replace("_", " ").title()
        
        if self._period in WEEKDAY_PERIODS:
            period_name = f"{period_name} Average"
        elif self._is_average:
            period_name = f"{period_name} Average"

        self._attr_name = f"{self._display_name} {period_name}"

        # Set device info to group sensors for this zone under one device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{person_entity}_{zone_slug}")},
            name=f"{display_name} Tracking",
            manufacturer="Person Zone Time Tracker",
            model="Zone Time Tracking",
            entry_type=None,
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        zone_data = self.coordinator.data.get(self._zone_entity_id)
        if not zone_data:
            return None

        total_hours = zone_data.get(self._period, 0.0)
        
        # If this is an average sensor, calculate daily average
        if self._is_average:
            from homeassistant.util import dt as dt_util
            now = dt_util.now()
            
            if self._period == PERIOD_TODAY:
                # Today average is just the total (1 day)
                return total_hours
            elif self._period == PERIOD_WEEK:
                # Days elapsed this week (Monday = 0)
                days_elapsed = now.weekday() + 1
                return round(total_hours / days_elapsed, 2) if days_elapsed > 0 else 0.0
            elif self._period == PERIOD_MONTH:
                # Days elapsed this month
                days_elapsed = now.day
                return round(total_hours / days_elapsed, 2) if days_elapsed > 0 else 0.0
            elif self._period in WEEKDAY_PERIODS:
                # Weekday averages are pre-calculated in coordinator
                return total_hours
        
        return total_hours

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return additional attributes."""
        return {
            ATTR_ZONE_NAME: self._display_name or self._zone_entity_id,
            ATTR_PERSON_ENTITY: self._person_entity,
            ATTR_PERIOD: self._period,
            ATTR_BACKFILLED: self._backfilled,
            ATTR_LAST_UPDATED: self.coordinator.last_update_success_time.isoformat()
            if self.coordinator.last_update_success_time
            else None,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
