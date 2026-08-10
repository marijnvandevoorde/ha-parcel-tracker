"""Carrier scrapers for Parcel Tracker."""
from __future__ import annotations
import logging
import re
import time
from dataclasses import dataclass, field
import requests
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "nl-BE,nl;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 15


@dataclass
class TrackerConfig:
    """API keys and settings passed through to scrapers."""

    dhl_api_key: str = ""
    pkge_api_key: str = ""
    # bpost's API returns NO_DATA_FOUND for most parcels unless the
    # destination postal code is supplied alongside the tracking number.
    postal_code: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Carrier auto-detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_carrier(tracking_number: str) -> str:  # noqa: PLR0911
    """Auto-detect carrier from tracking number format.

    Patterns ordered most-specific first to avoid false matches.
    Sources: UPU S10, carrier developer docs, ship24, parceldetect.
    """
    tn = tracking_number.strip().upper()

    # ── UPS ──────────────────────────────────────────────────────────────────
    # 1Z + 16 alphanumeric — globally unique prefix, zero conflicts
    if re.match(r"^1Z[A-Z0-9]{16}$", tn):
        return "ups"

    # ── bPost (Belgian Post) ─────────────────────────────────────────────────
    # - JD0 + 14 digits: IPC cross-border barcode used by bPost
    # - 323 + 9 digits: legacy 12-digit domestic label
    # - 3232/3299 + 14-20 digits: modern 18/24-digit domestic barcodes
    # - JJBEA + 22 alphanumeric: bPost certified mail format
    # - [A-Z]{2} + 9 digits + BE: UPU S10 for items sent from Belgium
    if re.match(
        r"^(JD0\d{14}|323\d{9}|(3232|3299)\d{14,20}|JJBEA[A-Z0-9]{22}|[A-Z]{2}\d{9}BE)$",
        tn,
    ):
        return "bpost"

    # ── PostNL (Dutch Post) ──────────────────────────────────────────────────
    # - [23]S + 11 or 13 alphanumeric: domestic consumer barcode (13 or 15 chars total)
    # - [A-Z]{2} + 9 digits + NL: UPU S10 for items destined for the Netherlands
    # Note: 3S prefix is also used by DHL Paket — PostNL wins in NL/BE context
    if re.match(r"^([23]S[A-Z0-9]{11}|[23]S[A-Z0-9]{13}|[A-Z]{2}\d{9}NL)$", tn):
        return "postnl"

    # ── DHL Germany (DHL Paket .de) ──────────────────────────────────────────
    # - JVGL + 6-14 alphanumeric: DHL Paket label barcode (NOT PostNL)
    # - JJD + 12-18 digits: DHL Paket domestic GLS-style barcode
    # - [A-Z]{2} + 8-9 digits + DE: UPU S10 ending in DE (e.g. CD662144845DE)
    if re.match(r"^(JVGL[A-Z0-9]{6,14}|JJD\d{12,18}|[A-Z]{2}\d{8,9}DE)$", tn):
        return "dhl_de"

    # ── DHL Express / eCommerce ──────────────────────────────────────────────
    # - JD + 18 digits: standard DHL Express international waybill
    # - GM + 16-20 digits: DHL eCommerce GlobalMail cross-border
    if re.match(r"^(JD\d{18}|GM\d{16,20})$", tn):
        return "dhl"

    # ── 4PX / China Post / ePacket ───────────────────────────────────────────
    # - 4PX + alphanumeric: proprietary 4PX Express format
    # - [A-Z]{2} + exactly 9 digits + CN: UPU S10 from China (China Post, EMS,
    #   ePacket, Yanwen, Cainiao all share this format)
    if re.match(r"^(4PX[A-Z0-9]+|[A-Z]{2}\d{9}CN)$", tn):
        return "fourpx"

    # ── DPD ──────────────────────────────────────────────────────────────────
    # 14-digit codes starting with 0 (Belgium & Germany standard)
    if re.match(r"^0\d{13}$", tn):
        return "dpd"

    # ── TNT / FedEx ──────────────────────────────────────────────────────────
    # Most-specific FedEx formats first to avoid ambiguity:
    # - 96 + 18-20 digits: FedEx Ground standard barcode prefix
    # - 22 digits: FedEx Freight
    # - 20 digits: FedEx SmartPost
    # - 15 digits: FedEx Ground (without 96 prefix)
    # - 12 digits: FedEx Express (also used by some DHL; lower confidence)
    # - 8-9 digits: TNT Express Europe (legacy, still common in BE/NL)
    if re.match(r"^96\d{18,20}$", tn):
        return "tnt"
    if re.match(r"^(\d{22}|\d{20}|\d{15}|\d{12}|\d{8,9})$", tn):
        return "tnt"

    return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(url: str) -> BeautifulSoup | None:
    """Perform GET request and return BeautifulSoup object."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        _LOGGER.warning("Request failed for %s: %s", url, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# pkge.net — universal fallback for DPD and 4PX
# ─────────────────────────────────────────────────────────────────────────────

# pkge.net integer status codes → our status strings
_PKGE_STATUS_MAP: dict[int, str] = {
    -1: "pending",   # Receiving status (not started yet)
    0: "pending",    # Added, not yet updated
    1: "pending",    # First update in progress
    2: "unknown",    # Updated but no info received
    3: "in_transit", # In transit
    4: "out_for_delivery",  # At delivery point
    5: "delivered",  # Delivered to recipient
    6: "exception",  # Failed delivery attempt
    7: "exception",  # Delivery error (package destroyed etc.)
    8: "pending",    # Info received, not yet sent
    9: "in_transit", # End of tracked route
}

# pkge.net courier ids to register packages with, per carrier key.
# courierId -1 (auto-detect) regularly fails to attach ANY courier, leaving
# the package stuck on "Pending" forever. Full list: GET /v1/couriers.
# 1897 = DPD Belgium — adjust for other countries (124 = DPD Germany, ...).
_PKGE_COURIER_IDS: dict[str, int] = {
    "dpd": 1897,
}


def _scrape_pkgenet(
    tracking_number: str,
    carrier: str,
    pkge_api_key: str,
    tracking_url: str,
) -> dict:
    """Fetch tracking via pkge.net API.

    pkge.net uses a register-then-poll model:
    1. GET existing package → if not found, POST to register, then GET again.
    2. Map integer status code to our status strings.
    Supports DPD, 4PX, China Post and 400+ other carriers.
    """
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": carrier,
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
    }

    pkge_headers = {
        "X-Api-Key": pkge_api_key,
        "Accept": "application/json",
    }
    get_url = "https://api.pkge.net/v1/packages"
    params = {"trackNumber": tracking_number}

    try:
        # Step 1: try fetching an already-registered package
        resp = requests.get(get_url, params=params, headers=pkge_headers, timeout=TIMEOUT)

        if resp.status_code == 404 or resp.status_code == 200 and _pkge_not_found(resp):
            # Not registered yet — add it (POST)
            add_resp = requests.post(
                get_url,
                params={
                    "trackNumber": tracking_number,
                    "courierId": _PKGE_COURIER_IDS.get(carrier, -1),
                },
                headers=pkge_headers,
                timeout=TIMEOUT,
            )
            if add_resp.status_code == 200:
                add_data = add_resp.json() if add_resp.text else {}
                # Code 905 = monthly add-limit reached
                if add_data.get("code") == 905:
                    result["status_detail"] = (
                        "pkge.net: maandlimiet van 50 pakketten bereikt. "
                        "Upgrade via business.pkge.net of verwijder ongebruikte pakketten."
                    )
                    return result
            elif add_resp.status_code == 401:
                result["status_detail"] = "pkge.net: ongeldige API-sleutel"
                return result
            # Short wait then fetch the now-registered package
            time.sleep(1)
            resp = requests.get(get_url, params=params, headers=pkge_headers, timeout=TIMEOUT)

        # Handle auth errors
        if resp.status_code == 401:
            result["status_detail"] = "pkge.net: ongeldige API-sleutel"
            return result
        if resp.status_code != 200:
            result["status_detail"] = f"pkge.net HTTP {resp.status_code}"
            return result

        try:
            data = resp.json()
        except ValueError:
            result["status_detail"] = "pkge.net: geen geldig JSON antwoord"
            return result

        payload = data.get("payload")
        if not payload or not isinstance(payload, dict):
            result["status_detail"] = "pkge.net: geen data ontvangen"
            return result

        status_int = payload.get("status", -1)
        result["status"] = _PKGE_STATUS_MAP.get(status_int, "unknown")

        # Best status detail: latest checkpoint title + location, or last_status
        checkpoints = payload.get("checkpoints") or []
        last_status = payload.get("last_status", "")

        if checkpoints and checkpoints[0].get("title"):
            cp = checkpoints[0]
            detail = cp["title"]
            location = cp.get("location", "")
            if location:
                detail = f"{detail} — {location}"
            result["status_detail"] = detail
        elif last_status and last_status not in ("Receiving status...", ""):
            result["status_detail"] = last_status
        else:
            result["status_detail"] = "Aangemeld, wacht op eerste scan"
            if status_int == -1:
                result["status"] = "pending"

    except Exception as exc:
        _LOGGER.error("pkge.net error for %s/%s: %s", carrier, tracking_number, exc)
        result["status_detail"] = str(exc)

    return result


def _pkge_not_found(resp: requests.Response) -> bool:
    """Return True if pkge.net response indicates package is not registered."""
    try:
        data = resp.json()
        code = data.get("code", 200)
        # 404-equivalent codes or empty payload
        return code not in (200,) or not data.get("payload")
    except (ValueError, AttributeError):
        return True


# ─────────────────────────────────────────────────────────────────────────────
# bPost
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_bpost(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "afgeleverd", "delivered", "overhandigd",
        "livré", "livre", "remis", "zugestellt",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "onderweg naar", "out for delivery", "bij de bode", "bezorgd wordt",
        "en cours de livraison", "en livraison", "in zustellung",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "in transit", "onderweg", "gesorteerd", "verwerkt", "aangeboden",
        "en transit", "en cours", "acheminé", "achemine",
        "unterwegs", "sortiert", "weitergeleitet",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "aangemeld", "registered", "ontvangen", "order",
        "enregistré", "enregistre", "pris en charge",
        "angemeldet", "abgeholt",
    ]):
        return "pending"
    if any(w in raw for w in [
        "probleem", "exception", "fout", "onbestelbaar",
        "incident", "échec", "echeç", "retourné", "retourne",
        "fehler", "nicht zustellbar", "rückläufer",
    ]):
        return "exception"
    return "unknown"


def scrape_bpost(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape bPost tracking via their API endpoint."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "bpost",
        "tracking_number": tracking_number,
        "tracking_url": f"https://track.bpost.cloud/btr/web/#/search?itemCode={tracking_number}&lang=nl",
    }
    try:
        # bpost returns NO_DATA_FOUND for most parcels unless the destination
        # postal code is supplied — query with it first, fall back without.
        postal = (config.postal_code if config else "") or ""
        urls = [
            "https://track.bpost.cloud/track/items?"
            f"itemIdentifier={tracking_number}&postalCode={postal}&lang=nl",
            "https://track.bpost.cloud/track/items?"
            f"itemIdentifier={tracking_number}&lang=nl",
        ]
        if not postal:
            urls = urls[1:]
        data = None
        for api_url in urls:
            resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code != 200:
                result["status_detail"] = f"HTTP {resp.status_code}"
                continue
            try:
                candidate = resp.json()
            except ValueError:
                result["status_detail"] = "Invalid response from bPost API"
                continue
            if candidate.get("items"):
                data = candidate
                break
            result["status_detail"] = "Pakket niet gevonden bij bPost"
        if data:
            item = data["items"][0]
            events = item.get("events", [])
            if events:
                # Events carry per-language descriptions under "key"
                # ({"NL": {"description": ...}, "EN": ...}), not a "label".
                latest = events[0]
                key = latest.get("key") or {}
                raw_status = (
                    (key.get("NL") or {}).get("description")
                    or (key.get("EN") or {}).get("description")
                    or latest.get("label", "")
                )
                location = (latest.get("location") or {}).get("locationName", "").strip()
                when = " ".join(
                    p for p in [latest.get("date", ""), latest.get("time", "")] if p
                )
                detail = raw_status
                if location:
                    detail += f" ({location})"
                if when:
                    detail += f" — {when}"
                result["status_detail"] = detail
                result["status"] = _normalize_bpost(raw_status)
            else:
                result["status"] = "pending"
                result["status_detail"] = "Aangemeld bij bPost"
    except Exception as exc:
        _LOGGER.error("bPost scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Colis Privé (experimental)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_colisprive(raw: str) -> str:
    """Normalize a Colis Privé event label (French or Dutch) to a status."""
    raw = raw.lower()
    if any(w in raw for w in [
        "incident", "retour", "refus", "échec", "echec",
        "non livré", "non livre", "anomalie",
        "mislukt", "niet bezorgd", "geweigerd", "probleem",
    ]):
        return "exception"
    if any(w in raw for w in [
        "livré", "livre au destinataire", "remis",
        "bezorgd", "geleverd", "afgeleverd", "overhandigd",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "en cours de livraison", "en tournée", "en tournee", "livraison en cours",
        "in bezorging", "bezorgronde", "onderweg naar u",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "transit", "achemin", "arrivé", "arrive sur", "tri",
        "expédié", "expedie", "pris en charge par",
        "onderweg", "sorteer", "verzonden", "in behandeling", "aangenomen",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "enregistré", "enregistre", "annoncé", "annonce",
        "préparation", "preparation", "attente",
        "aangekondigd", "geregistreerd", "aangemeld", "wachten",
    ]):
        return "pending"
    return "unknown"


def _colisprive_detail_url(num_colis: str) -> str:
    return (
        "https://colisprive.com/moncolis/pages/detailColis.aspx?"
        f"numColis={num_colis}&lang=NL"
    )


def scrape_colisprive(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape Colis Privé tracking via their public detail page.

    The page is an ASP.NET app; we warm up the session via the tracking
    iframe, then parse the event table rows (tr.bandeauText) of the detail
    page. Newest event comes first.

    Colis Privé identifies a parcel by parcel number + destination postal
    code concatenated (e.g. 780016616739 + 9090 → numColis=7800166167399090).
    If the number as given is not found and a postal code is configured,
    we retry with the postal code appended.
    """
    tn = tracking_number.strip().replace(" ", "")
    postal = ((config.postal_code if config else "") or "").strip()
    candidates = [tn]
    if postal and not tn.endswith(postal):
        candidates.append(tn + postal)
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "colisprive",
        "tracking_number": tn,
        "tracking_url": _colisprive_detail_url(tn),
    }
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        # Warm up ASP.NET session cookies via the public tracking iframe.
        session.get(
            "https://colisprive.com/moncolis/colis-iframe.aspx?lang=NL",
            timeout=TIMEOUT,
        )
        for num_colis in candidates:
            detail_url = _colisprive_detail_url(num_colis)
            resp = session.get(detail_url, timeout=TIMEOUT, allow_redirects=True)
            # Unknown parcels get redirected away from the detail page.
            if resp.status_code != 200 or "detailcolis" not in resp.url.lower():
                result["status_detail"] = "Colis niet gevonden bij Colis Privé"
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            events = []
            for row in soup.select("tr.bandeauText"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    date = cells[0].get_text(" ", strip=True)
                    label = cells[1].get_text(" ", strip=True)
                    if label:
                        events.append((date, label))
            if events:
                date, label = events[0]
                result["status_detail"] = f"{label} — {date}" if date else label
                result["status"] = _normalize_colisprive(label)
                result["tracking_url"] = detail_url
                break
            result["status_detail"] = "Geen tracking-events gevonden"
    except Exception as exc:
        _LOGGER.error("Colis Privé scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# PostNL
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_postnl(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "afgeleverd", "delivered", "bezorgd",
        "livré", "livre", "remis", "zugestellt",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "onderweg naar u", "bezorger", "out for delivery",
        "en cours de livraison", "en livraison", "livreur",
        "in zustellung", "mit dem zusteller",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "onderweg", "gesorteerd", "in transit", "verwerkt",
        "en transit", "en cours", "acheminé", "achemine",
        "unterwegs", "sortiert",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "verwacht", "aangemeld", "registered",
        "enregistré", "enregistre", "attendu",
        "angemeldet", "erwartet",
    ]):
        return "pending"
    if any(w in raw for w in [
        "niet", "probleem", "exception",
        "incident", "échec", "echeç", "retourné", "retourne",
        "nicht", "fehler", "rückläufer",
    ]):
        return "exception"
    return "unknown"


def scrape_postnl(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape PostNL via their tracking API."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "postnl",
        "tracking_number": tracking_number,
        "tracking_url": f"https://postnl.nl/tracktrace/?B={tracking_number}&P=",
    }
    try:
        api_url = (
            f"https://jouw.postnl.nl/track-and-trace/api/trackAndTrace/{tracking_number}"
            "?language=NL&expectedDeliveryTimeframeV2=true"
        )
        headers = {**HEADERS, "x-requested-with": "XMLHttpRequest"}
        resp = requests.get(api_url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                result["status_detail"] = "Invalid response from PostNL API"
                return result
            colli = data.get("colli", {})
            if colli:
                first = next(iter(colli.values()))
                status_phase = first.get("statusPhase", {})
                status_phrase = status_phase.get("message", "") or status_phase.get("header", "")
                if not status_phrase:
                    status_phrase = first.get("status", {}).get("message", "")
                result["status_detail"] = status_phrase or "Geen statusdetail beschikbaar"
                result["status"] = _normalize_postnl(status_phrase) if status_phrase else "pending"
            else:
                result["status_detail"] = "Pakket niet gevonden bij PostNL"
        elif resp.status_code == 404:
            result["status"] = "pending"
            result["status_detail"] = "Nog niet ingescand bij PostNL"
        else:
            result["status_detail"] = f"PostNL HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("PostNL scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# DHL (Express + Germany) — official DHL Developer API or website fallback
# ─────────────────────────────────────────────────────────────────────────────

# DHL Unified API statusCode strings → our status
_DHL_STATUS_CODES = {
    "delivered": "delivered",
    "in-transit": "in_transit",
    "transit": "in_transit",
    "out-for-delivery": "out_for_delivery",
    "delivery-failure": "exception",
    "failure": "exception",
    "pre-transit": "pending",
    "return": "exception",
    "unknown": "unknown",
}


def _normalize_dhl(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "delivered", "afgeleverd", "delivered to", "zugestellt",
        "livré", "livre", "remis",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "out for delivery", "with delivery courier", "bezorger", "in zustellung",
        "en cours de livraison", "en livraison", "livreur",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "transit", "departed", "arrived", "processed", "clearance",
        "doorgestuurd", "forwarded", "unterwegs", "weitergeleitet",
        "en transit", "en cours", "acheminé", "achemine", "transfert",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "picked up", "shipment picked", "registered", "aangemeld", "abgeholt",
        "enregistré", "enregistre", "pris en charge",
    ]):
        return "pending"
    if any(w in raw for w in [
        "exception", "delay", "held", "failed", "mislukt", "retour",
        "incident", "échec", "echeç", "retourné", "retourne",
    ]):
        return "exception"
    return "unknown"


def _scrape_dhl_api(
    tracking_number: str,
    carrier: str,
    api_key: str,
    tracking_url: str,
) -> dict:
    """Call the official DHL Unified Tracking API (developer.dhl.com).

    Covers DHL Express, DHL eCommerce and DHL Paket Germany.
    Free tier: 250 calls/day, register at developer.dhl.com.
    """
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": carrier,
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
    }
    try:
        resp = requests.get(
            "https://api-eu.dhl.com/track/shipments",
            params={"trackingNumber": tracking_number},
            headers={**HEADERS, "DHL-API-Key": api_key},
            timeout=TIMEOUT,
        )
        if resp.status_code == 429:
            result["status_detail"] = "DHL API: daglimiet bereikt (250/dag). Probeer het morgen opnieuw."
            return result
        if resp.status_code == 401:
            result["status_detail"] = "DHL API: ongeldige API-sleutel. Controleer via developer.dhl.com."
            return result
        if resp.status_code == 404:
            result["status"] = "pending"
            result["status_detail"] = "Zending nog niet gevonden bij DHL"
            return result
        if resp.status_code != 200:
            result["status_detail"] = f"DHL API HTTP {resp.status_code}"
            return result

        try:
            data = resp.json()
        except ValueError:
            result["status_detail"] = "DHL API: geen geldig JSON antwoord"
            return result

        shipments = data.get("shipments", [])
        if not shipments:
            result["status_detail"] = "Zending niet gevonden bij DHL"
            return result

        s = shipments[0]
        status_obj = s.get("status", {})
        description = status_obj.get("description", "")
        # DHL API returns statusCode at status level
        status_code = status_obj.get("statusCode", "").lower().replace("_", "-")
        events = s.get("events", [])

        result["status"] = (
            _DHL_STATUS_CODES.get(status_code)
            or _normalize_dhl(description)
        )
        # Use most recent event description for detail if available
        if events:
            ev = events[0]
            ev_desc = ev.get("description", description)
            loc = ev.get("location", {}).get("address", {}).get("addressLocality", "")
            result["status_detail"] = f"{ev_desc} — {loc}" if loc else ev_desc
        else:
            result["status_detail"] = description or "Geen statusdetail beschikbaar"

    except Exception as exc:
        _LOGGER.error("DHL API error for %s: %s", tracking_number, exc)
        result["status_detail"] = str(exc)

    return result


def scrape_dhl(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape DHL Express / eCommerce tracking.

    Uses official DHL Developer API if api_key is configured,
    falls back to demo-key (rate-limited: ~5 requests/day).
    """
    tracking_url = (
        f"https://www.dhl.com/be-nl/home/tracking/tracking-parcel.html"
        f"?submit=1&tracking-id={tracking_number}"
    )
    api_key = (config.dhl_api_key if config else "") or "demo-key"
    return _scrape_dhl_api(tracking_number, "dhl", api_key, tracking_url)


def scrape_dhl_de(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape DHL Germany (DHL Paket).

    With a DHL API key: uses official Unified API (also covers DHL Paket Germany).
    Without a key: falls back to DHL.de internal website API (no rate limit,
    but may break if DHL changes their website).
    """
    tracking_url = (
        f"https://www.dhl.de/de/privatkunden/dhl-sendungsverfolgung.html"
        f"?piececode={tracking_number}"
    )

    if config and config.dhl_api_key:
        return _scrape_dhl_api(tracking_number, "dhl_de", config.dhl_api_key, tracking_url)

    # ── Fallback: DHL.de internal website API (no key needed) ────────────────
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "dhl_de",
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
    }
    try:
        api_url = (
            "https://www.dhl.de/int-verfolgen/search"
            f"?lang=de&domain=de&type=p&fullResponse=true&investigationNumbers={tracking_number}"
        )
        headers = {**HEADERS, "Accept": "application/json", "Referer": tracking_url}
        resp = requests.get(api_url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                result["status_detail"] = "DHL Germany: geen geldig antwoord"
                return result

            sendungen = data.get("sendungen", [])
            if sendungen:
                s = sendungen[0]
                verlauf = (
                    s.get("sendungsdetails", {})
                     .get("sendungsverlauf", {})
                )
                events = verlauf.get("events", [])
                kurzstatus = verlauf.get("kurzstatus", "")
                aktuell = verlauf.get("aktuellerStatus", "")

                if events:
                    ev = events[0]
                    status_text = (
                        ev.get("status", "")
                        or ev.get("beschreibung", "")
                        or kurzstatus
                    )
                    result["status_detail"] = aktuell or status_text
                    result["status"] = _normalize_dhl(status_text) or _normalize_dhl(aktuell)
                elif kurzstatus or aktuell:
                    result["status_detail"] = aktuell or kurzstatus
                    result["status"] = _normalize_dhl(aktuell or kurzstatus)
                else:
                    result["status"] = "pending"
                    result["status_detail"] = "Aangemeld bij DHL Germany"
            else:
                result["status_detail"] = "Zending niet gevonden bij DHL Germany"
        else:
            result["status_detail"] = f"DHL Germany HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("DHL Germany scrape error: %s", exc)
        result["status_detail"] = str(exc)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# UPS
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_ups(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "delivered", "afgeleverd",
        "livré", "livre", "remis", "zugestellt",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "out for delivery", "on the way",
        "en cours de livraison", "en livraison",
        "in zustellung", "zur zustellung",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "in transit", "departed", "arrived", "processed", "export",
        "en transit", "en cours", "acheminé", "achemine",
        "unterwegs", "sortiert", "weitergeleitet",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "label created", "order processed", "pickup",
        "étiquette créée", "etiquette cree", "prise en charge",
        "label erstellt", "abgeholt", "angemeldet",
    ]):
        return "pending"
    if any(w in raw for w in [
        "exception", "delay", "held",
        "incident", "retard", "retourné", "retourne",
        "fehler", "verzögerung", "nicht zustellbar",
    ]):
        return "exception"
    return "unknown"


def scrape_ups(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape UPS tracking page."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "ups",
        "tracking_number": tracking_number,
        "tracking_url": f"https://www.ups.com/track?loc=nl_BE&tracknum={tracking_number}",
    }
    try:
        api_url = (
            "https://webapis.ups.com/track/api/Track/GetStatus?"
            f"loc=nl_BE&tracknum={tracking_number}&InquiryNumber1={tracking_number}"
        )
        headers = {**HEADERS, "X-XSRF-TOKEN": ""}
        resp = requests.get(api_url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                result["status_detail"] = "Invalid response from UPS API"
                return result
            pkgs = data.get("trackDetails", [])
            if pkgs:
                pkg = pkgs[0]
                activity = pkg.get("shipmentProgressActivities", [])
                status_desc = pkg.get("packageStatusDescription", "")
                result["status_detail"] = status_desc
                result["status"] = _normalize_ups(status_desc)
                if activity:
                    result["status_detail"] = activity[0].get("activityScanDescription", status_desc)
            else:
                result["status_detail"] = "Zending niet gevonden bij UPS"
        else:
            result["status_detail"] = f"UPS HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("UPS scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TNT / FedEx
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_tnt(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "delivered", "afgeleverd",
        "livré", "livre", "remis", "zugestellt",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "on fedex vehicle", "out for delivery", "on vehicle",
        "en cours de livraison", "en livraison",
        "in zustellung", "mit dem zusteller",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "in transit", "departed", "arrived", "at fedex", "clearance",
        "en transit", "en cours", "acheminé", "achemine",
        "unterwegs", "sortiert", "weitergeleitet",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "picked up", "shipment information", "label",
        "pris en charge", "enregistré", "enregistre",
        "abgeholt", "angemeldet", "label erstellt",
    ]):
        return "pending"
    if any(w in raw for w in [
        "exception", "delay", "held",
        "incident", "retard", "retourné", "retourne",
        "fehler", "verzögerung", "nicht zustellbar",
    ]):
        return "exception"
    return "unknown"


def scrape_tnt(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape TNT/FedEx tracking."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "tnt",
        "tracking_number": tracking_number,
        "tracking_url": f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    }
    try:
        api_url = (
            "https://www.fedex.com/trackingCal/track?"
            f"tracknumbers={tracking_number}&action=trackpackages&locale=nl_BE&version=1&format=json"
        )
        resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                result["status_detail"] = "Invalid response from FedEx API"
                return result
            packages = (
                data.get("TrackPackagesResponse", {})
                    .get("packageList", [])
            )
            if packages:
                pkg = packages[0]
                key_status = pkg.get("keyStatus", "")
                result["status_detail"] = key_status
                result["status"] = _normalize_tnt(key_status)
            else:
                result["status_detail"] = "Zending niet gevonden bij FedEx/TNT"
        else:
            result["status_detail"] = f"FedEx HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("TNT scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# DPD — pkge.net if key available, otherwise session-based scrape
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_dpd(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "delivered", "afgeleverd", "zugestellt", "bezorgd",
        "livré", "livre", "remis",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "out for delivery", "in zustellung", "bezorger", "onderweg naar u",
        "en cours de livraison", "en livraison", "livreur",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "transit", "depot", "hub", "unterwegs", "onderweg", "sorted",
        "en transit", "en cours", "acheminé", "achemine", "transfert",
        "sortiert", "weitergeleitet",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "pickup", "collected", "abgeholt", "aangemeld", "label",
        "pris en charge", "enregistré", "enregistre",
        "angemeldet", "label erstellt",
    ]):
        return "pending"
    if any(w in raw for w in [
        "exception", "failed", "nicht", "problem", "retour",
        "incident", "échec", "echeç", "retourné", "retourne",
        "fehler", "nicht zustellbar", "rückläufer",
    ]):
        return "exception"
    return "unknown"


def scrape_dpd(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape DPD tracking.

    With a pkge.net API key: uses pkge.net (reliable, 50 pakketten/maand gratis).
    Without a key: attempts direct session-based scraping of DPD REST API
    (may fail due to bot protection).
    """
    tracking_url = f"https://tracking.dpd.de/parcelstatus?query={tracking_number}&language=nl"

    if config and config.pkge_api_key:
        return _scrape_pkgenet(tracking_number, "dpd", config.pkge_api_key, tracking_url)

    # ── Fallback: session-based direct scrape ────────────────────────────────
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "dpd",
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
    }
    try:
        with requests.Session() as session:
            # Load main page first to pick up session cookies and bypass bot protection
            session.get(
                "https://tracking.dpd.de/",
                headers={**HEADERS, "Accept": "text/html"},
                timeout=TIMEOUT,
            )
            api_url = f"https://tracking.dpd.de/rest/plc/{tracking_number}"
            api_headers = {
                **HEADERS,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": tracking_url,
                "Origin": "https://tracking.dpd.de",
            }
            resp = session.get(api_url, headers=api_headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                result["status_detail"] = (
                    "DPD API: geen JSON ontvangen (bot-beveiliging). "
                    "Stel een pkge.net API-sleutel in voor betrouwbare DPD-tracking."
                )
                return result
            parcel_lifecycle = data.get("parcellifecycleResponse", {})
            status_info = parcel_lifecycle.get("parcelLifeCycleData", {})
            scan_info = status_info.get("statusInfo", [])
            if scan_info:
                latest = scan_info[0]
                label = (
                    latest.get("label", {}).get("content", [""])[0]
                    if latest.get("label", {}).get("content")
                    else ""
                )
                result["status_detail"] = label
                result["status"] = _normalize_dpd(label)
            else:
                result["status"] = "pending"
                result["status_detail"] = "Aangemeld bij DPD"
        elif resp.status_code == 404:
            result["status"] = "pending"
            result["status_detail"] = "Pakket nog niet ingescand bij DPD"
        else:
            result["status_detail"] = (
                f"DPD HTTP {resp.status_code}. "
                "Stel een pkge.net API-sleutel in voor betrouwbare DPD-tracking."
            )
    except Exception as exc:
        _LOGGER.error("DPD scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 4PX / China Post — pkge.net if key available, otherwise direct API
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_fourpx(raw: str) -> str:
    raw = raw.lower()
    if any(w in raw for w in [
        "delivered", "afgeleverd", "zugestellt",
        "livré", "livre", "remis", "签收", "已签收",
    ]):
        return "delivered"
    if any(w in raw for w in [
        "out for delivery", "delivering", "bezorger",
        "en livraison", "in zustellung", "派送中",
    ]):
        return "out_for_delivery"
    if any(w in raw for w in [
        "transit", "departed", "arrived", "processed", "clearance",
        "en transit", "unterwegs", "acheminé", "achemine",
        "transport", "customs", "douane", "zoll", "in transit",
        "已发出", "运输中", "到达", "离开",
    ]):
        return "in_transit"
    if any(w in raw for w in [
        "picked up", "registered", "accepted", "aangemeld",
        "enregistré", "enregistre", "angemeldet",
        "已收件", "揽收",
    ]):
        return "pending"
    if any(w in raw for w in [
        "exception", "failed", "delay", "held",
        "incident", "retard", "fehler", "verzögerung",
        "异常", "退回",
    ]):
        return "exception"
    return "unknown"


def _parse_fourpx_response(data: dict) -> tuple[str, str]:
    """Try multiple 4PX response structures. Returns (status, status_detail)."""
    # Structure 1: data.data.items[].events[].description
    items = data.get("data", {}).get("items", [])
    if not items:
        # Structure 2: data.data.list[].trackList[].remark
        items = data.get("data", {}).get("list", [])
    if not items:
        # Structure 3: data.list[]
        items = data.get("list", [])
    if not items:
        # Structure 4: data directly as list
        raw = data.get("data", [])
        if isinstance(raw, list):
            items = raw

    if not items:
        return "", ""

    item = items[0]

    # Try events[] first
    events = item.get("events", []) or item.get("trackList", [])
    if events:
        ev = events[0]
        desc = (
            ev.get("description", "")
            or ev.get("remark", "")
            or ev.get("detail", "")
            or ev.get("content", "")
        )
        return _normalize_fourpx(desc), desc

    # Try top-level status fields
    desc = (
        item.get("latestEvent", {}).get("description", "")
        or item.get("status", "")
        or item.get("statusDesc", "")
    )
    if desc:
        return _normalize_fourpx(desc), desc

    return "pending", "Aangemeld bij 4PX"


def scrape_fourpx(tracking_number: str, config: TrackerConfig | None = None) -> dict:
    """Scrape 4PX / China Post tracking.

    With a pkge.net API key: uses pkge.net (reliable, 50 pakketten/maand gratis).
    Without a key: attempts direct 4PX API (may be blocked by bot protection).
    """
    tracking_url = f"https://track.4px.com/#/result/0/{tracking_number}"

    if config and config.pkge_api_key:
        return _scrape_pkgenet(tracking_number, "fourpx", config.pkge_api_key, tracking_url)

    # ── Fallback: direct 4PX API ─────────────────────────────────────────────
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "fourpx",
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
    }
    try:
        api_url = "https://track.4px.com/api/v2/track"
        payload = {"numbers": [tracking_number]}
        headers = {
            **HEADERS,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://track.4px.com/",
            "Origin": "https://track.4px.com",
        }
        resp = requests.post(api_url, json=payload, headers=headers, timeout=TIMEOUT)
        _LOGGER.debug("4PX response %s: %.200s", resp.status_code, resp.text)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                result["status_detail"] = (
                    "4PX API: geen JSON ontvangen (bot-beveiliging). "
                    "Stel een pkge.net API-sleutel in voor betrouwbare 4PX-tracking."
                )
                return result
            status, detail = _parse_fourpx_response(data)
            if status:
                result["status"] = status
                result["status_detail"] = detail
            else:
                result["status_detail"] = "4PX: geen trackingdata gevonden (mogelijk nog niet ingescand)"
                result["status"] = "pending"
        else:
            result["status_detail"] = (
                f"4PX HTTP {resp.status_code}. "
                "Stel een pkge.net API-sleutel in voor betrouwbare 4PX-tracking."
            )
    except Exception as exc:
        _LOGGER.error("4PX scrape error: %s", exc)
        result["status_detail"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

SCRAPER_MAP = {
    "bpost": scrape_bpost,
    "postnl": scrape_postnl,
    "dhl": scrape_dhl,
    "dhl_de": scrape_dhl_de,
    "dpd": scrape_dpd,
    "ups": scrape_ups,
    "tnt": scrape_tnt,
    "fourpx": scrape_fourpx,
    "colisprive": scrape_colisprive,
}


def get_tracking_info(
    tracking_number: str,
    carrier: str = "auto",
    config: TrackerConfig | None = None,
) -> dict:
    """Main entry point: detect carrier if needed, then scrape.

    Args:
        tracking_number: The parcel tracking number.
        carrier: Carrier key or "auto" for auto-detection.
        config: Optional API keys and settings passed to scrapers.
    """
    if not tracking_number or not tracking_number.strip():
        return {"status": "unknown", "status_detail": "No tracking number", "carrier": carrier}

    if carrier == "auto":
        carrier = detect_carrier(tracking_number)

    scraper = SCRAPER_MAP.get(carrier)
    if scraper:
        return scraper(tracking_number, config)

    return {
        "status": "unknown",
        "status_detail": f"Unsupported carrier: {carrier}",
        "carrier": carrier,
        "tracking_number": tracking_number,
        "tracking_url": "",
    }
