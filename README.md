# Parcel Tracker — Home Assistant Custom Integration

Een custom integratie voor Home Assistant waarmee je pakketjes van meerdere vervoerders rechtstreeks kunt volgen vanuit je smart home dashboard. Geen externe apps, geen handmatig controleren — de status van je pakket verschijnt automatisch als een sensor in Home Assistant en kan worden gebruikt in automations, meldingen en dashboards.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)

---

## Wat doet deze integratie?

Parcel Tracker verbindt Home Assistant met de track & trace systemen van de grote Belgische en Nederlandse vervoerders. Je voert een trackingnummer in, en de integratie herkent automatisch de vervoerder en haalt de actuele bezorgstatus op. Die status wordt beschikbaar als een HA-sensor, zodat je er automations op kunt bouwen — zoals een melding op je telefoon wanneer je pakket bezorgd is.

Tot **10 pakketjes tegelijk** kunnen worden gevolgd. De status wordt automatisch elke 30 minuten ververst.

---

## Ondersteunde vervoerders

| Vervoerder | Auto-detectie | Methode |
|------------|--------------|---------|
| bPost | Ja | Officiële API |
| PostNL | Ja | Officiële API |
| DHL | Ja | API + HTML fallback |
| UPS | Ja | API |
| TNT / FedEx | Ja | FedEx JSON API |

---

## Mogelijkheden

- **Automatische vervoerdersherkenning** — plak een trackingnummer in en de integratie detecteert zelf de vervoerder op basis van het nummerformaat
- **10 sensorslots** — elk met eigen status, vervoerder, trackingnummer en directe link naar de trackingpagina
- **Automatische verversing** elke 30 minuten
- **Geen YAML nodig** — volledig in te stellen via de Home Assistant UI
- **Bijwerken zonder herinstalleren** — trackingnummers aanpassen via de opties
- **Nederlands en Engels** — interface beschikbaar in beide talen

---

## Statussen

Elke sensor toont een van de volgende statussen:

| Status | Betekenis |
|--------|-----------|
| `pending` | Pakket aangemeld maar nog niet opgehaald |
| `in_transit` | Onderweg |
| `out_for_delivery` | Wordt vandaag bezorgd |
| `delivered` | Bezorgd |
| `exception` | Probleem met bezorging |
| `unknown` | Status niet beschikbaar |

---

## Installatie

### Via HACS (aanbevolen)

1. Open HACS → Integraties → ⋮ → Aangepaste repositories
2. Voeg toe: `https://github.com/wwoutt/ha-parcel-tracker`
3. Categorie: **Integratie**
4. Klik op **Downloaden**
5. Herstart Home Assistant

### Handmatig

1. Kopieer de map `custom_components/parcel_tracker/` naar je HA config-map
2. Herstart Home Assistant

---

## Instellen

1. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**
2. Zoek op **Parcel Tracker**
3. Vul trackingnummers in en kies de vervoerder (of gebruik Auto-detect)
4. Sensoren verschijnen als `sensor.parcel_1` t/m `sensor.parcel_10`

---

## Sensorattributen

Elke sensor bevat:

- `state` — huidige bezorgstatus
- `tracking_number` — het trackingnummer
- `carrier` — de vervoerder
- `status_detail` — leesbare omschrijving van de vervoerder zelf
- `tracking_url` — directe link naar de trackingpagina

---

## Voorbeeldautomation

```yaml
automation:
  - alias: "Melding bij bezorging"
    trigger:
      - platform: state
        entity_id: sensor.parcel_1
        to: delivered
    action:
      - service: notify.mobile_app
        data:
          message: "Je pakket is bezorgd!"
```

---

## Beperkingen

- Sommige vervoerders gebruiken JavaScript of CAPTCHA's — status kan soms `unknown` tonen
- UPS en DHL kunnen frequente opvragen beperken (rate limiting)
- Bedoeld voor persoonlijk/thuisgebruik

---

## Gemaakt met AI

Deze integratie is ontwikkeld met behulp van **Claude** (AI van Anthropic). De volledige code — inclusief vervoerdersintegraties, carrier-detectie, sensorlogica en Home Assistant configuratieflow — is gegenereerd en uitgewerkt in samenwerking met Claude Code.

---

## Licentie

MIT
