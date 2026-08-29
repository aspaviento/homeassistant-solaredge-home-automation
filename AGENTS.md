# Agent Guidance

## Project Scope

This repository is the public source for a Home Assistant custom integration
installable through HACS. It exposes SolarEdge Home Automation devices from the
SolarEdge monitoring web API, including SolarEdge Smart Devices and the
integrated SolarEdge EV Charger.

The API used here is not a public SolarEdge API. Keep the repository private
operationally safe even though the repository itself is public.

## Repository Layout

- `custom_components/solaredge_home_automation/`: Home Assistant integration
  source.
- `README.md`: public installation, usage, and limitation documentation.
- `hacs.json`: HACS repository metadata.
- `custom_components/solaredge_home_automation/manifest.json`: Home Assistant
  integration metadata, including version.

## Public Safety

Do not commit real SolarEdge usernames, passwords, cookies, bearer tokens,
site IDs, device IDs, serial numbers, vehicle identifiers, local hostnames,
private URLs, schedules, or household device names in tracked examples.

Use synthetic payloads for tests and documentation. Real deployment notes,
current IDs, and operational observations belong in the private operations
repository, not in public documentation.

## Home Assistant Integration Rules

- Preserve the integration domain: `solaredge_home_automation`.
- Keep setup config-entry based; do not add YAML-only setup.
- Keep polling conservative because the API is cloud-backed and undocumented.
- Prefer read-only sensors for state and explicit `button` entities for
  operations that change charger state.
- Do not model the EV Charger as a simple switch unless the state mapping is
  proven reliable for all relevant states.
- Keep Smart Device state based on the SolarEdge `status.level` field.
- Smart Device manual on/off uses the same `activationState` endpoint as EV
  Charger charge/stop. Keep those controls explicit buttons.
- Treat schedule editing, Excess Solar, Use Battery, Smart Device Auto mode,
  Smart Device timer controls, Connected Car settings, Charging History, and
  charger Settings as future work until their undocumented endpoints have been
  captured and manually tested.

## HACS And Releases

Keep HACS metadata valid:

- `hacs.json`
- `custom_components/solaredge_home_automation/manifest.json`
- README installation instructions

For HACS-visible releases, update the integration version, commit, tag, and
publish a GitHub release. HACS should install from a stable tag such as
`v0.1.0`, not from local manual copies or short commit references.

Do not deploy changes to a live Home Assistant instance by directly copying
files into `custom_components` once the integration is managed through HACS,
unless the user explicitly authorizes that exception. Home Assistant restart is
separately authorized and normally user-owned.

## Validation

Before committing code changes, run:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/solaredge-home-automation-pycache python3 -m compileall custom_components/solaredge_home_automation
python3 -m json.tool custom_components/solaredge_home_automation/manifest.json >/dev/null
python3 -m json.tool hacs.json >/dev/null
git diff --check
```

Before publishing, scan for private household details using project-appropriate
terms from the private operations repo, not by committing those terms here.
