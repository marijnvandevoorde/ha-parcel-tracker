# CLAUDE.md — Parcel Tracker (ha-parcel-tracker)

## Projectoverzicht
Home Assistant custom integration voor het bijhouden van pakketjes via een zijbalk-panel.
Repository: https://github.com/wwoutt/ha-parcel-tracker

### Wat het doet
- Sidebar-panel in HA om pakketjes toe te voegen, te bewerken en te verwijderen
- Automatisch ophalenvan tracking-status bij meerdere carriers
- Ondersteunde carriers: bPost, DHL (internationaal), DHL Germany, DPD, 4PX/China Post, TNT/FedEx, UPS, PostNL
- Meertalig panel (NL/FR/EN)
- Maximaal 10 pakketjes tegelijk
- Persistente opslag via HA Store
- Automatisering-services: `parcel_tracker.add_parcel` en `parcel_tracker.remove_parcel`
- Dynamische sensor-entities (worden aangemaakt/verwijderd op basis van actieve pakketjes)

### Technische stack
- `__init__.py` — setup, panel registratie, services, static paths
- `coordinator.py` — DataUpdateCoordinator, haalt status op via scrapers
- `scrapers.py` — carrier scrapers + auto-detect
- `sensor.py` — dynamische sensor entities
- `ws_api.py` — WebSocket API voor het panel
- `frontend/parcel-tracker-panel.js` — custom web component (Shadow DOM)
- `const.py` — constanten, carriers, versie
- `config_flow.py` — vereenvoudigde config flow (geen formulier, meteen aanmaken)
- `translations/` — HA-vertalingen voor hassfest

---

## ⚠️ PRIORITEIT 1 — NOOIT COMMITTEN OF PUSHEN ZONDER TOESTEMMING

**NOOIT** `git add`, `git commit`, `git push` of een GitHub release uitvoeren zonder dat de gebruiker expliciet toestemming geeft.
- Bestanden lokaal aanpassen mag wel
- Na het aanpassen: melden wat er klaarstaat, dan wachten op "commit" of "push" van de gebruiker
- Dit geldt ook als de gebruiker eerder in het gesprek toestemming gaf — elke commit/push heeft een nieuwe bevestiging nodig

---

## Werkafspraken

### Versiebeheer
- Bij elke nieuwe functionaliteit of bugfix de versie ophogen in **alle drie**:
  - `custom_components/parcel_tracker/const.py` → `VERSION = "x.x.x"`
  - `custom_components/parcel_tracker/manifest.json` → `"version": "x.x.x"`
  - `README.md` → badge `![Version](https://img.shields.io/badge/version-x.x.x-green)`
- De versie in README, manifest en const.py moet altijd identiek zijn
- Patch (x.x.**1**) voor bugfixes, minor (x.**1**.0) voor nieuwe features

### Taal
- Antwoord altijd in het **Nederlands**
- Code en comments mogen in het Engels blijven

### HACS / hassfest validatie
- `manifest.json` sleutels moeten in volgorde staan: `domain`, `name`, dan alfabetisch
- `after_dependencies: ["http"]` is verplicht voor static path registratie
- `translations/en.json` en `nl.json` moeten `config.step.user` en `options.step.init` bevatten
- Geen formulier in de config flow — integratie wordt direct aangemaakt

### HA-specifieke regels
- Scrapers zijn synchroon (`requests`) → altijd via `hass.async_add_executor_job()` aanroepen, nooit `asyncio.get_event_loop().run_in_executor()`
- Panel JS-URL krijgt `?v={VERSION}` voor cache-busting
- Panel wordt één keer geregistreerd via de `_panel_registered` flag

### Code kwaliteit
- Elke scraper moet altijd een betekenisvolle `status_detail` teruggeven, ook bij lege resultaten of fouten
- `resp.json()` altijd wrappen in `try/except ValueError`
- Bij status `unknown` of `exception` toont het panel de `status_detail` in oranje

---

## Wat we tot nu toe gedaan hebben

### v1.0 – v1.5 (begin)
- Basisintegratie opgezet met tracking via bPost, PostNL, DHL, UPS, TNT
- GitHub repository aangemaakt: `wwoutt/ha-parcel-tracker`
- HACS-validatie en hassfest-fouten opgelost (manifest volgorde, vertalingen, topics, brand icon)

### v1.6 – v1.7 (sidebar panel)
- Zijbalk-panel toegevoegd als custom web component
- WebSocket API (`parcel_tracker/list`, `set_parcel`, `refresh`)
- Persistente opslag via HA `Store`
- Config flow vereenvoudigd: geen formulier meer bij installatie

### v1.8 (uitbreidingen)
- DPD en DHL Germany toegevoegd als carriers
- Meertaligheid toegevoegd aan panel (NL/FR/EN)
- Dynamische sensor entities (auto aanmaken/verwijderen)
- Automatisering-services `add_parcel` en `remove_parcel`
- Laatste controle-tijdstip en handmatige refresh-knop in panel
- README bijgewerkt (Engelstalig)

### v1.9 (bugfixes & taaluitbreiding)
- Franse en Duitse keywords toegevoegd aan alle status-normalizers
- DHL Germany auto-detect toegevoegd (`^[A-Z]{2}\d{8,9}[A-Z]{2}$`)
- DHL Germany eigen scraper met `_DHL_STATUS_CODES` mapping (betrouwbaarder dan tekstnormalisatie)
- DPD JSON-crash opgelost met `try/except ValueError`

### v1.10.1
- 4PX / China Post carrier toegevoegd (scraper, normalizer, auto-detect, panel)
- Coordinator gebruikt nu `hass.async_add_executor_job` (correcte HA-methode)
- Debug-logging per pakket toegevoegd in coordinator
- Alle scrapers geven nu een duidelijke melding als een pakket niet gevonden wordt
- Panel toont `status_detail` in oranje bij `unknown`/`exception` status
- Fallback-hint in panel als er geen detail beschikbaar is

### v1.10.2
- DHL Germany: overgestapt van rate-limited demo-key API naar DHL.de's eigen interne website-API (`/int-verfolgen/search`)
- DPD: session-gebaseerde aanpak (eerst cookies ophalen, dan AJAX-call) — foute HTML-fallback verwijderd
- 4PX: hulpfunctie `_parse_fourpx_response` die meerdere response-structuren probeert, betere foutmeldingen

### v1.11.0 (huidig)
- **DHL Developer API** geïntegreerd: `scrape_dhl` en `scrape_dhl_de` gebruiken nu de officiële DHL Unified Tracking API (`api-eu.dhl.com`) wanneer een API-sleutel is ingesteld (gratis, 250/dag, registreer op developer.dhl.com). Zonder sleutel: fallback naar demo-key (DHL Express) of DHL.de website-API (DHL Germany).
- **pkge.net API** geïntegreerd: `scrape_dpd` en `scrape_fourpx` gebruiken pkge.net wanneer een API-sleutel is ingesteld (gratis, 50 pakketten/maand, registreer op business.pkge.net). Zonder sleutel: bestaande fallback-scrapers.
- `TrackerConfig` dataclass toegevoegd in `scrapers.py` voor het doorgeven van API-sleutels aan scrapers
- `config_flow.py`: opties-stap toegevoegd met formulier voor DHL en pkge.net API-sleutels (in HA via Instellingen → Integraties → Parcel Tracker → Configureren)
- `coordinator.py`: leest API-sleutels uit `entry.options` en geeft ze door als `TrackerConfig`
- `strings.json` + vertalingen (`nl.json`, `en.json`) bijgewerkt met opties-formulier inclusief beschrijvingen en links naar registratiepagina's
- Alle scraper-functies hebben nu een optionele `config: TrackerConfig | None` parameter

---

## Bekende openstaande issues
- Geen bekende open issues
