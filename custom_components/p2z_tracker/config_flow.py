"""Adds config flow for Person Zone Time Tracker."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zone
from homeassistant.helpers import entity_registry as er, selector

from .const import (
    CONF_BACKFILL_DAYS,
    CONF_DISPLAY_NAME,
    CONF_ENABLE_BACKFILL,
    CONF_PERSON_ENTITY,
    CONF_RETENTION_DAYS,
    CONF_TRACKED_ZONES,
    CONF_ZONE_NAME,
    DEFAULT_RETENTION_DAYS,
    DOMAIN,
    LOGGER,
)


class P2ZTrackerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Person Zone Time Tracker."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            # Validate person entity exists
            person_entity = user_input[CONF_PERSON_ENTITY]
            entity_reg = er.async_get(self.hass)
            if not entity_reg.async_get(person_entity):
                errors[CONF_PERSON_ENTITY] = "invalid_person"
            else:
                # Create config entry with person entity
                # Zones will be added via options flow
                return self.async_create_entry(
                    title=f"Zone Tracking: {person_entity}",
                    data={CONF_PERSON_ENTITY: person_entity},
                    options={CONF_TRACKED_ZONES: []},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PERSON_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="person"),
                    ),
                },
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> P2ZTrackerOptionsFlow:
        """Get the options flow for this handler."""
        return P2ZTrackerOptionsFlow(config_entry)


class P2ZTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Person Zone Time Tracker."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._current_zones: list[dict[str, Any]] = list(
            config_entry.options.get(CONF_TRACKED_ZONES, [])
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_zone_menu()

    async def async_step_zone_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show zone management menu."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add_zone":
                return await self.async_step_add_zone()
            elif action == "remove_zone" and self._current_zones:
                return await self.async_step_remove_zone()

        # Build menu options
        menu_options = ["add_zone"]
        if self._current_zones:
            menu_options.append("remove_zone")

        # Show current zones
        zones_text = "\n".join(
            [
                f"- {z.get(CONF_DISPLAY_NAME, z[CONF_ZONE_NAME])}"
                for z in self._current_zones
            ]
        )
        description_placeholders = {
            "current_zones": zones_text if zones_text else "No zones tracked yet"
        }

        return self.async_show_menu(
            step_id="zone_menu",
            menu_options=menu_options,
            description_placeholders=description_placeholders,
        )

    async def async_step_add_zone(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add a new zone to track."""
        errors = {}

        if user_input is not None:
            zone_name = user_input[CONF_ZONE_NAME]

            # Check if zone already tracked
            if any(z[CONF_ZONE_NAME] == zone_name for z in self._current_zones):
                errors[CONF_ZONE_NAME] = "already_configured"
            else:
                # Add zone to tracked list
                new_zone = {
                    CONF_ZONE_NAME: zone_name,
                    CONF_DISPLAY_NAME: user_input.get(CONF_DISPLAY_NAME, ""),
                    CONF_ENABLE_BACKFILL: user_input.get(CONF_ENABLE_BACKFILL, False),
                    CONF_BACKFILL_DAYS: user_input.get(CONF_BACKFILL_DAYS, 0),
                    CONF_RETENTION_DAYS: user_input.get(
                        CONF_RETENTION_DAYS, DEFAULT_RETENTION_DAYS
                    ),
                    CONF_ENABLE_AVERAGES: user_input.get(CONF_ENABLE_AVERAGES, False),
                }
                self._current_zones.append(new_zone)
                
                LOGGER.info(
                    "Added zone %s to tracking. Total zones: %d",
                    zone_name,
                    len(self._current_zones),
                )

                # Save and return to menu
                return self.async_create_entry(
                    title="",
                    data={CONF_TRACKED_ZONES: self._current_zones},
                )

        # Get all available zones
        all_zones = self.hass.states.async_entity_ids("zone")
        zone_options = [
            selector.SelectOptionDict(value=entity_id, label=entity_id)
            for entity_id in all_zones
        ]

        return self.async_show_form(
            step_id="add_zone",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ZONE_NAME): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=zone_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Optional(CONF_DISPLAY_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(),
                    ),
                    vol.Optional(CONF_ENABLE_BACKFILL, default=False): selector.BooleanSelector(),
                    vol.Optional(CONF_BACKFILL_DAYS, default=7): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=365,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    vol.Optional(
                        CONF_RETENTION_DAYS, default=DEFAULT_RETENTION_DAYS
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=3650,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        ),
                    ),
                    vol.Optional(CONF_ENABLE_AVERAGES, default=False): selector.BooleanSelector(),
                },
            ),
            errors=errors,
        )

    async def async_step_remove_zone(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Remove a tracked zone."""
        if user_input is not None:
            zone_to_remove = user_input["zone_to_remove"]
            self._current_zones = [
                z for z in self._current_zones if z[CONF_ZONE_NAME] != zone_to_remove
            ]

            # Save and return to menu
            return self.async_create_entry(
                title="",
                data={CONF_TRACKED_ZONES: self._current_zones},
            )

        # Build list of removable zones
        zone_options = [
            selector.SelectOptionDict(
                value=z[CONF_ZONE_NAME],
                label=z.get(CONF_DISPLAY_NAME, z[CONF_ZONE_NAME]),
            )
            for z in self._current_zones
        ]

        return self.async_show_form(
            step_id="remove_zone",
            data_schema=vol.Schema(
                {
                    vol.Required("zone_to_remove"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=zone_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                },
            ),
        )
