# Person Zone Time Tracker

[![GitHub Release](https://img.shields.io/github/release/xyz00777/hacs_p2z_tracker.svg?style=for-the-badge)](https://github.com/xyz00777/hacs_p2z_tracker/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

**Person Zone Time Tracker** is a Home Assistant custom integration that automatically tracks and calculates the time a person entity spends in different zones. It replaces manual YAML configuration of `history_stats` and `utility_meter` sensors with an easy-to-use UI-based configuration flow.

## Features

- **UI-Based Configuration** - No YAML editing required! Configure everything through the Home Assistant UI
- **Automatic Sensor Creation** - Creates 3 sensors per tracked zone:
  - **Today** - Time spent in the zone today
  - **Week** - Time spent in the zone this week (Monday to now)
  - **Month** - Time spent in the zone this month
- **Historical Backfill** - Optionally initialize sensors with historical data when adding a new zone
- **Configurable Retention** - Set custom data retention periods per zone
- **Multiple Zone Tracking** - Track as many zones as you need for a person

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/xyz00777/hacs_p2z_tracker`
6. Select category: "Integration"
7. Click "Add"
8. Find "Person Zone Time Tracker" in HACS and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub releases](https://github.com/xyz00777/hacs_p2z_tracker/releases)
2. Extract the `p2z_tracker` folder to your `custom_components` directory
3. Restart Home Assistant

### Building from Source

To create a ZIP file for manual upload:

**Normal Linux**:
```bash
./scripts/build.sh
# Creates build/p2z_tracker-{version}.zip
```

**NixOS**:
```bash
./scripts/build-nixos.sh
# Automatically sets up nix-shell with zip and dependencies
# Creates build/p2z_tracker-{version}.zip
```

Then upload the ZIP file to your Home Assistant instance and extract it to `custom_components/`.

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Person Zone Time Tracker"
4. Select the person entity you want to track
5. Click **Submit**

### Adding Zones to Track

After initial setup, add zones through the integration's options:

1. Go to **Settings** → **Devices & Services**
2. Find "Person Zone Time Tracker" integration
3. Click **Configure**
4. Select **Add new zone to track**
5. Configure the zone:
   - **Zone**: Select the zone entity (e.g., `zone.home`, `zone.work`)
   - **Display Name** (optional): Friendly name for the sensors
   - **Enable Historical Backfill**: Check to initialize with past data
   - **Days to Backfill**: Number of days of historical data to load (if backfill enabled)
   - **Data Retention Period**: How long to keep historical data (default: 90 days)
6. Click **Submit**

## Sensor Naming

Sensors are automatically created with the following naming pattern:

```
sensor.p2z_{person}_{zone}_{period}
```

**Example**:
For person `person.john` tracking zone `zone.work`:
- `sensor.p2z_john_work_today` - Hours at work today
- `sensor.p2z_john_work_week` - Hours at work this week
- `sensor.p2z_john_work_month` - Hours at work this month

## Sensor Details

Each sensor provides:
- **State**: Time in hours (decimal, e.g., `8.5` = 8 hours 30 minutes)
- **Device Class**: Duration
- **Unit**: Hours
- **Attributes**:
  - `zone_name` - Friendly zone name
  - `person_entity` - Tracked person entity
  - `period` - Time period (today/week/month)
  - `backfilled` - Whether historical data was loaded
  - `last_updated` - Last update timestamp

## Use Cases

- **Work Hours Tracking** - Monitor time spent at work each day/week/month
- **Home Time Analysis** - See how much time you spend at home
- **Location Insights** - Track time at parents', friends', or other frequent locations
- **Custom Dashboards** - Build visualizations with the sensor data

## Comparison with YAML Configuration

### Before (YAML):
```yaml
sensor:
  - platform: history_stats
    name: "Time at Work Today"
    entity_id: person.john
    state: "work"
    type: time
    start: "{{ today_at('00:00') }}"
    end: "{{ now() }}"

utility_meter:
  work_weekly:
    source: sensor.time_at_work_today
    cycle: weekly
```

## Troubleshooting

### Sensors not updating
- Check that the person entity is correctly configured
- Ensure the zone entities exist
- Verify the recorder integration is working properly

### Historical backfill not working
- Make sure you have sufficient history in your Home Assistant database
- Check the recorder retention settings
- Verify the person was actually in the zone during the backfill period

### Sensors showing 0.0
- The person may not have been in the zone during the time period
- Check if the zone name matches the person's state (e.g., `home` not `zone.home`)

## About This Project

> **Note**: This integration was created with AI assistance. As the maintainer, I don't have extensive Python or Home Assistant development experience, so I'm relying on AI tools to help build this integration. If you find issues or have suggestions for improvements, please don't hesitate to open an issue or submit a PR - your contributions are very welcome and appreciated! 🙏

## Contributing

Contributions are welcome and encouraged! Whether it's bug fixes, new features, code improvements, or documentation updates - all PRs are appreciated.

If you'd like to contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

I'm happy to review and merge community contributions!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

Found a bug or have a feature request? Please [open an issue](https://github.com/xyz00777/hacs_p2z_tracker/issues) on GitHub.
