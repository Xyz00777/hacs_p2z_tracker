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
