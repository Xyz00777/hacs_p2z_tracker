# Template Sensor Examples

These examples show how to create advanced sensors using the data from Person Zone Time Tracker.

## Using the Developer Tools

Home Assistant has a built-in template editor that allows you to test these templates before adding them to your configuration.

1. Go to **Developer Tools** > **Template**.
2. Paste any of the example codes below into the editor.
3. Replace `<username>` and `<zone>` with your actual entity parts (e.g., `xyz00777` and `work`).
4. The result will appear on the right side, showing you exactly what the sensor value would be.

## Configuration Examples

Add these to your `configuration.yaml` under the `template:` section.

```yaml
template:
  - sensor:
      # Example 1: Daily average for the current week
      - name: "Work Week Average"
        unique_id: work_week_average
        unit_of_measurement: "h"
        state: >
          {% set today = states('sensor.p2z_<username>_<zone>_today') | float(0) %}
          {% set week = states('sensor.p2z_<username>_<zone>_week') | float(0) %}
          {% set days = now().weekday() + 1 %}
          {{ (week / days) | round(2) if days > 0 else 0 }}
        icon: mdi:chart-line

      # Example 2: Goal tracker (40 hours per week)
      - name: "Work Week Goal Progress"
        unique_id: work_week_goal
        unit_of_measurement: "%"
        state: >
          {% set week = states('sensor.p2z_<username>_<zone>_week') | float(0) %}
          {% set goal = 40 %}
          {{ ((week / goal) * 100) | round(0) }}
        icon: mdi:target

      # Example 3: Comparison with last month
      - name: "Work Time Change"
        unique_id: work_time_change
        unit_of_measurement: "h"
        state: >
          {% set current = states('sensor.p2z_<username>_<zone>_month') | float(0) %}
          {% set history = state_attr('sensor.p2z_<username>_<zone>_month', 'last_month') | float(0) %}
          {{ (current - history) | round(2) }}
        icon: mdi:trending-up

      # Example 4: Predicted monthly total
      - name: "Work Month Prediction"
        unique_id: work_month_prediction
        unit_of_measurement: "h"
        state: >
          {% set days_passed = now().day %}
          {% set days_in_month = now().replace(day=28).replace(month=now().month % 12 + 1).replace(day=1).replace(hour=0, minute=0, second=0, microsecond=0) - now().replace(day=1).replace(hour=0, minute=0, second=0, microsecond=0) %}
          {% set days_in_month = days_in_month.days %}
          {% set current = states('sensor.p2z_<username>_<zone>_month') | float(0) %}
          {% set daily_avg = current / days_passed if days_passed > 0 else 0 %}
          {{ (daily_avg * days_in_month) | round(2) }}
        icon: mdi:crystal-ball

      # Example 5: Time remaining to reach weekly goal
      - name: "Work Hours Remaining"
        unique_id: work_hours_remaining
        unit_of_measurement: "h"
        state: >
          {% set week = states('sensor.p2z_<username>_<zone>_week') | float(0) %}
          {% set goal = 40 %}
          {% set remaining = goal - week %}
          {{ remaining if remaining > 0 else 0 }}
        icon: mdi:clock-outline

      # Example 6: Multiple zones total
      - name: "Total Activity Time Today"
        unique_id: total_activity_today
        unit_of_measurement: "h"
        state: >
          {% set work = states('sensor.p2z_<username>_<zone1>_today') | float(0) %}
          {% set gym = states('sensor.p2z_<username>_<zone2>_today') | float(0) %}
          {% set errands = states('sensor.p2z_<username>_<zone3>_today') | float(0) %}
          {{ (work + gym + errands) | round(2) }}
        icon: mdi:clock-check

  - binary_sensor:
      # Example 7: Alert if daily goal not met
      - name: "Work Daily Goal Met"
        unique_id: work_daily_goal_met
        state: >
          {% set today = states('sensor.p2z_<username>_<zone>_today') | float(0) %}
          {{ today >= 8 }}
        icon: >
          {% if is_state('binary_sensor.work_daily_goal_met', 'on') %}
            mdi:check-circle
          {% else %}
            mdi:alert-circle
          {% endif %}

      # Example 8: Alert if over time limit
      - name: "Work Overtime Alert"
        unique_id: work_overtime_alert
        state: >
          {% set week = states('sensor.p2z_<username>_<zone>_week') | float(0) %}
          {{ week > 45 }}
        icon: mdi:alert
```
