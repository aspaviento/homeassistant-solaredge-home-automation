# SolarEdge Home Automation

Private Home Assistant custom integration for SolarEdge Home Automation devices.

This integration uses the SolarEdge monitoring web session to read the
undocumented Home Automation API. It is intended for private use with HACS.

## Scope

- Smart Devices returned by the SolarEdge Home Automation `/devices` endpoint.
- SolarEdge EV Charger status, current session data, schedule details, and
  explicit charge/stop buttons.

The existing official SolarEdge integration should remain responsible for site
production, grid import/export, battery, module statistics, and Energy
Dashboard data.

## Installation

1. Add this private repository to HACS as an integration repository.
2. Download the integration through HACS.
3. Restart Home Assistant.
4. Add **SolarEdge Home Automation** from Settings -> Devices & services.
5. Enter the SolarEdge site ID and monitoring account credentials.

## Notes

The API used here is not documented by SolarEdge and may change. Start with
read-only sensors and use charger buttons manually before building automations
on top.
