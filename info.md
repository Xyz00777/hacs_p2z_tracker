# Person Zone Time Tracker

Track the time a person spends in different zones automatically, with UI-based configuration.

## Features

✨ **Easy Setup** - Configure through Home Assistant UI, no YAML required

📊 **Automatic Sensors** - Creates time tracking sensors for each zone (today/week/month)

⏱️ **Historical Backfill** - Optional initialization with past data

🎯 **Multiple Zones** - Track as many locations as needed

## Quick Start

1. Add the integration via Settings → Integrations
2. Select a person entity to track
3. Add zones to track through the configuration options
4. View your sensors: `sensor.p2z_{person}_{zone}_{period}`

## Sensors

Each tracked zone creates 3 sensors:
- **Today**: Time in zone today (hours)
- **Week**: Time in zone this week (hours)
- **Month**: Time in zone this month (hours)

All sensors update every minute and display time in hours.
