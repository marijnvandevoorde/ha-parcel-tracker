# 📦 Parcel Tracker — Home Assistant Custom Integration

Track up to **10 parcels** simultaneously from bPost, DHL, TNT/FedEx, UPS and PostNL — directly in Home Assistant.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)

## Features

- 🔍 **Auto-detect** carrier from tracking number format
- 📊 **10 sensor slots** — each shows status, carrier, tracking URL
- 🔄 **Automatic refresh** every 30 minutes
- 🌍 **NL + EN** translations
- ⚙️ **Config Flow** — no YAML needed
- 🔧 **Options Flow** — update tracking numbers without reinstalling

## Supported Carriers

| Carrier | Auto-detect | Method |
|---------|------------|--------|
| bPost | ✅ | Official API |
| PostNL | ✅ | Official API |
| DHL | ✅ | API + HTML fallback |
| UPS | ✅ | API |
| TNT / FedEx | ✅ | FedEx JSON API |

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add: `https://github.com/YOUR_USERNAME/ha-parcel-tracker`
3. Category: **Integration**
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy `custom_components/parcel_tracker/` to your HA config folder
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Parcel Tracker**
3. Fill in tracking numbers + carrier (or use Auto-detect)
4. Sensors appear as `sensor.parcel_1` through `sensor.parcel_10`

## Sensor Attributes

Each sensor exposes:
- `state`: `delivered` | `in_transit` | `out_for_delivery` | `pending` | `exception` | `unknown`
- `tracking_number`
- `carrier`
- `status_detail` — human-readable status from the carrier
- `tracking_url` — direct link to tracking page

## Example Automation

```yaml
automation:
  - alias: "Notify when parcel delivered"
    trigger:
      - platform: state
        entity_id: sensor.parcel_1
        to: delivered
    action:
      - service: notify.mobile_app
        data:
          message: "📦 {{ state_attr('sensor.parcel_1', 'friendly_name') }} is bezorgd!"
```

## Limitations

- Some carriers use JavaScript-heavy pages or CAPTCHAs — status may occasionally show `unknown`
- UPS and DHL may rate-limit frequent requests
- For personal/home use only

## License

MIT
