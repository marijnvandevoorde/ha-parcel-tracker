# Parcel Tracker — Home Assistant Custom Integration

A custom Home Assistant integration that lets you track parcels from multiple carriers directly in your smart home. No external apps, no manual checking — parcel status appears automatically as sensor entities and can be used in automations, notifications, and dashboards.

> **Fork notice** — this is a fork of [wwoutt/ha-parcel-tracker](https://github.com/wwoutt/ha-parcel-tracker) that adds:
> - **bpost fix**: the bpost API needs the destination postal code (configurable in the integration options) and returns event descriptions under `key.NL/EN.description` — without these, bpost parcels showed `unknown`/not found
> - **Colis Privé** support (experimental, HTML scrape of the public detail page)
> - Planned: GLS (their open API now requires registered access), Mondial Relay

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)
[![Version](https://img.shields.io/badge/version-1.12.0-green)](https://github.com/marijnvandevoorde/ha-parcel-tracker/releases)

---

## What does it do?

Parcel Tracker connects Home Assistant to the track & trace systems of major carriers. Enter a tracking number, and the integration automatically identifies the carrier and retrieves the current delivery status. That status becomes available as a HA sensor entity — so you can build automations on top of it, like a notification when your parcel is delivered.

Up to **10 parcels** can be tracked simultaneously. Status is refreshed automatically every 30 minutes.

---

## Supported carriers

| Carrier | Auto-detect | Method |
|---------|------------|--------|
| bPost | Yes | Official API (set your postal code in the integration options) |
| PostNL | Yes | Official API |
| DHL (International) | Yes | API + HTML fallback |
| DHL Germany | No | API + HTML fallback |
| DPD | Yes | 17track API (key required; direct scrape fallback) |
| UPS | Yes | API |
| TNT / FedEx | Yes | FedEx JSON API |
| Colis Privé | No | HTML scrape (experimental) |
| GLS | No | 17track API (key required) |
| Mondial Relay | No | 17track API (key required) |

---

## Features

- **Sidebar panel** — manage all parcels from a dedicated page in the HA sidebar
- **Dynamic sensors** — a sensor entity is created when a parcel is added and removed when it is deleted
- **Automatic carrier detection** — paste a tracking number and the carrier is detected automatically
- **Automation support** — add and remove parcels via HA services
- **Multilingual panel** — the sidebar panel adapts to your HA language (English, Dutch, French)
- **No YAML needed** — fully configurable through the HA UI
- **Persistent storage** — parcel data survives HA restarts

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add: `https://github.com/wwoutt/ha-parcel-tracker`
3. Category: **Integration**
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/parcel_tracker/` folder to your HA config directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Parcel Tracker**
3. Click **Submit** — no configuration needed
4. The **Parcel Tracker** panel appears in the sidebar

---

## Managing parcels

Open the **Parcel Tracker** panel in the sidebar. From there you can:

- **Add** a parcel — enter a tracking number, carrier and optional name
- **Edit** an existing parcel
- **Delete** a parcel
- **Refresh** to fetch the latest status immediately

Each parcel gets its own sensor entity (e.g. `sensor.parcel_tracker_parcel_1`) that updates automatically.

---

## Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Parcel registered, not yet picked up |
| `in_transit` | On its way |
| `out_for_delivery` | Being delivered today |
| `delivered` | Delivered |
| `exception` | Delivery problem |
| `unknown` | Status unavailable |

---

## Sensor attributes

Each sensor exposes:

| Attribute | Description |
|-----------|-------------|
| `state` | Current delivery status |
| `tracking_number` | The tracking number |
| `carrier` | The carrier |
| `status_detail` | Human-readable status from the carrier |
| `tracking_url` | Direct link to the carrier's tracking page |

---

## Automation support

Parcels can be added and removed via HA services, making it easy to trigger them from automations, scripts, or the developer tools.

### Add a parcel

```yaml
service: parcel_tracker.add_parcel
data:
  tracking_number: "JD014600004860246190"
  carrier: auto               # optional — auto-detect by default
  friendly_name: "My order"   # optional
```

The service finds the first available slot automatically. If the tracking number already exists or all 10 slots are full, a warning is logged.

### Remove a parcel

```yaml
service: parcel_tracker.remove_parcel
data:
  tracking_number: "JD014600004860246190"
```

### Example: notify on delivery

```yaml
automation:
  - alias: "Notify when parcel is delivered"
    trigger:
      - platform: state
        entity_id: sensor.parcel_tracker_parcel_1
        to: delivered
    action:
      - service: notify.mobile_app
        data:
          message: "Your parcel has been delivered!"
```

### Example: add parcel from a notification or input

```yaml
automation:
  - alias: "Add parcel from input_text"
    trigger:
      - platform: state
        entity_id: input_button.add_parcel
    action:
      - service: parcel_tracker.add_parcel
        data:
          tracking_number: "{{ states('input_text.tracking_number') }}"
          carrier: auto
```

---

## Limitations

- Some carriers use JavaScript-heavy pages or CAPTCHAs — status may occasionally show `unknown`
- UPS and DHL may rate-limit frequent requests
- Intended for personal / home use only

---

## Built with AI

This integration was developed with the help of **Claude** (AI by Anthropic). The complete codebase — including carrier integrations, auto-detection, sensor logic, WebSocket API, sidebar panel, and Home Assistant config flow — was generated and refined in collaboration with Claude Code.

---

## License

MIT
