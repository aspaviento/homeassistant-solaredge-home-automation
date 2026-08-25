# SolarEdge Home Automation

Experimental Home Assistant custom integration for SolarEdge Home Automation
devices.

This integration uses the SolarEdge monitoring web session to read the
undocumented Home Automation API. It is intended for personal use through HACS.

## Experimental Status

This project is not affiliated with, endorsed by, or supported by SolarEdge.
It uses undocumented SolarEdge Monitoring endpoints that may change or stop
working without notice.

Use it only if you are comfortable with occasional breakage and manual recovery.
Start with read-only sensors and test charger controls manually before building
automations on top.

## Scope

- Smart Devices returned by the SolarEdge Home Automation `/devices` endpoint.
- SolarEdge EV Charger status, current session data, schedule details, and
  explicit charge/stop buttons.
- EV Charger charging, plugged-in, solar usage, available action, and
  connection diagnostics.
- Setup and options use a numeric scan interval input in minutes.

The existing official SolarEdge integration should remain responsible for site
production, grid import/export, battery, module statistics, and Energy
Dashboard data.

## Installation

1. Add this repository to HACS as an integration repository.
2. Download the integration through HACS.
3. Restart Home Assistant.
4. Add **SolarEdge Home Automation** from Settings -> Devices & services.
5. Enter the SolarEdge site ID and monitoring account credentials.

## Security Notes

The integration stores SolarEdge Monitoring credentials in Home Assistant's
config entry storage, like other cloud integrations. Do not share diagnostics
or logs that contain credentials, cookies, bearer tokens, site IDs, device IDs,
vehicle identifiers, or household device names.
