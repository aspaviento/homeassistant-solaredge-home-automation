# SolarEdge Home Automation

Experimental Home Assistant custom integration for SolarEdge Home Automation
devices.

This integration uses the SolarEdge monitoring web session to read the
undocumented Home Automation API. It is intended for personal use through HACS.

## Experimental Status

This project is not affiliated with, endorsed by, or supported by SolarEdge.
It uses undocumented SolarEdge Monitoring endpoints that may change or stop
working without notice.

Because the endpoints are undocumented, updates from SolarEdge may require a
manual integration update or reconfiguration. Controls should be tested manually
before being used in automations.

## Current Scope

- Smart Devices returned by the SolarEdge Home Automation `/devices` endpoint.
- Smart Device explicit manual turn-on and turn-off buttons.
- Smart Device Auto button.
- Smart Device timed manual turn-on service. SolarEdge `duration` is expressed
  in minutes.
- Smart Device timer duration number entity and a visible turn-on-for-timer
  button per Smart Device.
- SolarEdge EV Charger status, current session data, schedule details, and
  explicit charge/stop buttons.
- EV Charger charging, plugged-in, solar usage, available action, and
  connection diagnostics.
- Setup and options use a numeric scan interval input in minutes. The default
  is 15 minutes, matching the conservative polling cadence of the official
  SolarEdge Home Assistant integration.
- Changing options reloads the integration so the polling interval takes effect.

The official SolarEdge Home Assistant integration covers site production, grid
import/export, battery, module statistics, and Energy Dashboard data. This
integration focuses only on SolarEdge Home Automation devices that are not
covered by the official integration.

The integration creates a parent Home Assistant device named `SolarEdge Site
<site_id>` and connects Smart Devices and EV Chargers through that site device.

## Validated Controls

The following controls have been validated against a live SolarEdge Home
Automation installation:

- EV Charger charge now and stop charging.
- Smart Device manual turn on and turn off.
- Smart Device Auto mode.
- Smart Device turn on for timer, with duration expressed in minutes.

The Smart Device timer is exposed in Home Assistant as a per-device Timer
duration number entity and a Turn on for timer button. The timer end timestamp
and timer active binary sensor depend on the status fields returned by SolarEdge
after polling.

## Services

### `solaredge_home_automation.turn_on_for`

Turns on one or more Smart Energy devices manually for a duration in minutes.
This service is also exposed as visible per-device controls through the Timer
duration number entity and the Turn on for timer button.

Example:

```yaml
action: solaredge_home_automation.turn_on_for
data:
  entity_id:
    - binary_sensor.example_device_active
  duration: 5
```

## Current Limitations

- Schedule editing is not implemented.
- Excess Solar and Use Battery toggles are not implemented.
- Connected Car settings, Charging History, and charger Settings are not exposed
  as controls.

Additional controls may be added in later releases after their behavior is
validated.

## Installation

1. Add this repository to HACS as an integration repository.
2. Download the integration through HACS.
3. Restart Home Assistant.
4. Add **SolarEdge Home Automation** from Settings -> Devices & services.
5. Enter the SolarEdge site ID and monitoring account credentials.

## Security Notes

The integration stores SolarEdge Monitoring credentials in Home Assistant's
config entry storage, like other cloud integrations. Diagnostics or logs may
contain sensitive account, site, device, vehicle, or household information.
