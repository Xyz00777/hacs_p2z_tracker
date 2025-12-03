"""Custom types for p2z_tracker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import P2ZDataUpdateCoordinator


type P2ZTrackerConfigEntry = ConfigEntry[P2ZTrackerData]


@dataclass
class P2ZTrackerData:
    """Data for the Person Zone Time Tracker integration."""

    coordinator: P2ZDataUpdateCoordinator
    integration: Integration
