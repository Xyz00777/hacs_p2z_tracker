"""
Custom integration to integrate p2z_tracker with Home Assistant.

For more details about this integration, please refer to
https://github.com/xyz00777/hacs_p2z_tracker
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from .const import CONF_PERSON_ENTITY, DEFAULT_UPDATE_INTERVAL, DOMAIN, LOGGER
from .coordinator import P2ZDataUpdateCoordinator
from .data import P2ZTrackerData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import P2ZTrackerConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: P2ZTrackerConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = P2ZDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        config_entry=entry,
    )
    entry.runtime_data = P2ZTrackerData(
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    # Cleanup orphaned entities
    await _async_cleanup_orphaned_entities(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: P2ZTrackerConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: P2ZTrackerConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_cleanup_orphaned_entities(
    hass: HomeAssistant,
    entry: P2ZTrackerConfigEntry,
) -> None:
    """Remove entities that are no longer tracked."""
    from homeassistant.helpers import device_registry as dr, entity_registry as er
    from homeassistant.util import slugify

    from .const import (
        CONF_PERSON_ENTITY,
        CONF_TRACKED_ZONES,
        CONF_ZONE_NAME,
        PERIOD_MONTH,
        PERIOD_TODAY,
        PERIOD_WEEK,
    )

    entity_registry = er.async_get(hass)
    tracked_zones = entry.options.get(CONF_TRACKED_ZONES, [])
    person_entity = entry.data[CONF_PERSON_ENTITY]
    person_name = person_entity.replace("person.", "")
    periods = [PERIOD_TODAY, PERIOD_WEEK, PERIOD_MONTH]

    # Generate set of expected unique IDs
    expected_unique_ids = set()
    for zone_config in tracked_zones:
        zone_name = zone_config[CONF_ZONE_NAME]
        zone_slug = slugify(zone_name.replace("zone.", ""))
        for period in periods:
            expected_unique_ids.add(f"p2z_{person_name}_{zone_slug}_{period}")

    # Find and remove entities that are not in expected list
    entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    LOGGER.debug(
        "Checking cleanup: Found %d existing entities, expected %d unique IDs", 
        len(entries), 
        len(expected_unique_ids)
    )
    
    for entity in entries:
        if entity.unique_id not in expected_unique_ids:
            LOGGER.info("Removing orphaned entity: %s", entity.entity_id)
            entity_registry.async_remove(entity.entity_id)

    # Cleanup orphaned devices
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    
    # Generate set of expected device identifiers
    expected_device_ids = set()
    for zone_config in tracked_zones:
        zone_name = zone_config[CONF_ZONE_NAME]
        zone_slug = slugify(zone_name.replace("zone.", ""))
        expected_device_ids.add((DOMAIN, f"{person_name}_{zone_slug}"))
        
    for device in devices:
        # Check if device has any of our expected identifiers
        # A device matches if ANY of its identifiers match our expected list
        is_valid = False
        for identifier in device.identifiers:
            if identifier in expected_device_ids:
                is_valid = True
                break
        
        if not is_valid:
            LOGGER.debug(
                "Removing orphaned device: %s (identifiers: %s, expected: %s)", 
                device.name, 
                device.identifiers,
                expected_device_ids
            )
            device_registry.async_remove_device(device.id)
