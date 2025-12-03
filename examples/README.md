# Dashboard Examples

This folder contains example dashboard configurations for the Person Zone Time Tracker integration.

## Requirements

These examples use the **ApexCharts Card** custom component. Install it via HACS:
1. Go to HACS → Frontend
2. Search for "ApexCharts Card"
3. Install it

## Using the Examples

1. Open your Home Assistant dashboard in edit mode
2. Add a new card
3. Choose "Manual" or "Show Code Editor"
4. Copy the YAML from `dashboard.yaml`
5. **Replace the entity names** with your own sensor entities (e.g., replace `sensor.time_at_work_today` with your actual sensor)

## Available Sensors

After configuring a zone, you'll have 3 sensors per zone:
- `sensor.p2z_<person>_<zone>_today` - Time spent today
- `sensor.p2z_<person>_<zone>_week` - Time spent this week (Monday-Sunday)
- `sensor.p2z_<person>_<zone>_month` - Time spent this month

## Templates

See `templates.yaml` for examples of template sensors you can create for:
- Custom time periods
- Averages and comparisons
- Goal tracking
