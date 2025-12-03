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
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    ATTR_BACKFILLED,
    ATTR_LAST_UPDATED,
    ATTR_PERIOD,
    ATTR_PERSON_ENTITY,
    ATTR_ZONE_NAME,
    CONF_DISPLAY_NAME,
    CONF_ENABLE_BACKFILL,
    CONF_PERSON_ENTITY,
    CONF_TRACKED_ZONES,
    CONF_ZONE_NAME,
    PERIOD_MONTH,
    PERIOD_TODAY,
    PERIOD_WEEK,
)
from .coordinator import P2ZDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import P2ZTrackerConfigEntry


PERIODS = [PERIOD_TODAY, PERIOD_WEEK, PERIOD_MONTH]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: P2ZTrackerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    person_entity = entry.data[CONF_PERSON_ENTITY]
    tracked_zones = entry.options.get(CONF_TRACKED_ZONES, [])

    # Create 3 sensors per tracked zone (today, week, month)
    sensors = []
    for zone_config in tracked_zones:
        zone_name = zone_config[CONF_ZONE_NAME]
        display_name = zone_config.get(CONF_DISPLAY_NAME, zone_name)
        backfilled = zone_config.get(CONF_ENABLE_BACKFILL, False)

        for period in PERIODS:
            sensors.append(
                ZoneTimeSensor(
                    coordinator=coordinator,
                    person_entity=person_entity,
                    zone_entity_id=zone_name,
                    display_name=display_name,
                    period=period,
                    backfilled=backfilled,
                )
            )

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
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._person_entity = person_entity
        self._zone_entity_id = zone_entity_id
        self._display_name = display_name
        self._period = period
        self._backfilled = backfilled

        # Generate entity ID
        person_name = person_entity.replace("person.", "")
        zone_slug = slugify(zone_entity_id.replace("zone.", ""))
        self._attr_unique_id = f"p2z_{person_name}_{zone_slug}_{period}"
        self.entity_id = f"sensor.p2z_{person_name}_{zone_slug}_{period}"

        # Set name
        period_label = period.capitalize()
        self._attr_name = f"Time at {display_name} {period_label}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        zone_data = self.coordinator.data.get(self._zone_entity_id)
        if not zone_data:
            return None

        return zone_data.get(self._period, 0.0)

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
