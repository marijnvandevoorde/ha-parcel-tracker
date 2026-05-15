"""Carrier scrapers for Parcel Tracker."""
from __future__ import annotations
import logging
import re
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


def detect_carrier(tracking_number: str) -> str:
    """Auto-detect carrier from tracking number format."""
    tn = tracking_number.strip().upper()

    # bPost: 323xxxxxxxxx or JD0xxxxxxxxx or barcode starting with 32
    if re.match(r"^(323\d{9}|JD0\d{14}|3S[A-Z0-9]{10,})$", tn):
        return "bpost"
    # PostNL: 3S + 14 alphanumeric, or JVGL, or RR..NL
    if re.match(r"^(3S[A-Z0-9]{13}|JVGL[A-Z0-9]+|[A-Z]{2}\d{9}NL)$", tn):
        return "postnl"
    # DHL: JD015600\d{12} or 1Z... no (that's UPS), or numeric 10-12 digits
    if re.match(r"^(JD\d{18}|\d{10,12}|[A-Z0-9]{10}DHL)$", tn):
        return "dhl"
    # UPS: 1Z + 16 chars
    if re.match(r"^1Z[A-Z0-9]{16}$", tn):
        return "ups"
    # DPD: 14-digit codes starting with 0, or %05B prefix
    if re.match(r"^(0\d{13}|%05B\d+)$", tn):
        return "dpd"
    # TNT/FedEx: numeric 9, 12 or 15 digits, or GE..
    if re.match(r"^(\d{9}|\d{12}|\d{15}|[A-Z]{2}\d{9})$", tn):
        return "tnt"

    return "unknown"


def _get(url: str) -> BeautifulSoup | None:
    """Perform GET request and return BeautifulSoup object."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        _LOGGER.warning("Request failed for %s: %s", url, exc)
        return None


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


def scrape_bpost(tracking_number: str) -> dict:
    """Scrape bPost tracking via their API endpoint."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "bpost",
        "tracking_number": tracking_number,
        "tracking_url": f"https://track.bpost.cloud/btr/web/#/search?itemCode={tracking_number}&lang=nl",
    }
    try:
        api_url = (
            "https://track.bpost.cloud/track/items?"
            f"itemIdentifier={tracking_number}&lang=nl"
        )
        resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if items:
                item = items[0]
                events = item.get("events", [])
                if events:
                    latest = events[0]
                    raw_status = latest.get("label", "")
                    result["status_detail"] = raw_status
                    result["status"] = _normalize_bpost(raw_status)
                else:
                    result["status"] = "pending"
                    result["status_detail"] = "Aangemeld"
        else:
            result["status"] = "unknown"
            result["status_detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("bPost scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


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


def scrape_postnl(tracking_number: str) -> dict:
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
            data = resp.json()
            colli = data.get("colli", {})
            if colli:
                first = next(iter(colli.values()))
                status_phrase = first.get("statusPhase", {}).get("message", "")
                result["status_detail"] = status_phrase
                result["status"] = _normalize_postnl(status_phrase)
        elif resp.status_code == 404:
            result["status"] = "pending"
            result["status_detail"] = "Nog niet ingescand"
        else:
            result["status_detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("PostNL scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


# DHL API returns these status codes directly — more reliable than text normalization
_DHL_STATUS_CODES = {
    "delivered": "delivered",
    "in-transit": "in_transit",
    "transit": "in_transit",
    "out-for-delivery": "out_for_delivery",
    "delivery-failure": "exception",
    "pre-transit": "pending",
    "return": "exception",
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


def scrape_dhl(tracking_number: str) -> dict:
    """Scrape DHL via their tracking API."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "dhl",
        "tracking_number": tracking_number,
        "tracking_url": f"https://www.dhl.com/be-nl/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    }
    try:
        api_url = (
            f"https://api-eu.dhl.com/track/shipments?trackingNumber={tracking_number}"
        )
        headers = {
            **HEADERS,
            "DHL-API-Key": "demo-key",
        }
        resp = requests.get(api_url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            shipments = data.get("shipments", [])
            if shipments:
                s = shipments[0]
                events = s.get("events", [])
                status_obj = s.get("status", {})
                description = status_obj.get("description", "")
                status_code = status_obj.get("status", "").lower().replace("_", "-")
                result["status_detail"] = description
                # Prefer the API's own status code over text normalization
                result["status"] = (
                    _DHL_STATUS_CODES.get(status_code)
                    or _normalize_dhl(description)
                )
                if events:
                    result["status_detail"] = events[0].get("description", description)
        else:
            # Fallback: scrape HTML
            soup = _get(
                f"https://www.dhl.com/be-nl/home/tracking.html?tracking-id={tracking_number}"
            )
            if soup:
                el = soup.find(class_=re.compile(r"c-tracking-result__status"))
                if el:
                    raw = el.get_text(strip=True)
                    result["status_detail"] = raw
                    result["status"] = _normalize_dhl(raw)
    except Exception as exc:
        _LOGGER.error("DHL scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


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


def scrape_ups(tracking_number: str) -> dict:
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
            data = resp.json()
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
            result["status_detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("UPS scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


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


def scrape_tnt(tracking_number: str) -> dict:
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
            data = resp.json()
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
            result["status_detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("TNT scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


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


def scrape_dpd(tracking_number: str) -> dict:
    """Scrape DPD tracking via their REST API."""
    result = {
        "status": "unknown",
        "status_detail": "",
        "carrier": "dpd",
        "tracking_number": tracking_number,
        "tracking_url": f"https://tracking.dpd.de/parcelstatus?query={tracking_number}&language=nl",
    }
    try:
        api_url = f"https://tracking.dpd.de/rest/plc/{tracking_number}"
        resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            depot_data = data.get("depot", {})
            parcel_lifecycle = data.get("parcellifecycleResponse", {})
            status_info = parcel_lifecycle.get("parcelLifeCycleData", {})
            scan_info = status_info.get("statusInfo", [])
            if scan_info:
                latest = scan_info[0]
                label = latest.get("label", {}).get("content", [""])[0] if latest.get("label", {}).get("content") else ""
                result["status_detail"] = label
                result["status"] = _normalize_dpd(label)
            else:
                result["status"] = "pending"
                result["status_detail"] = "Aangemeld bij DPD"
        else:
            result["status_detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:
        _LOGGER.error("DPD scrape error: %s", exc)
        result["status"] = "unknown"
        result["status_detail"] = str(exc)
    return result


def scrape_dhl_de(tracking_number: str) -> dict:
    """Scrape DHL Germany — uses same DHL API but links to dhl.de."""
    result = scrape_dhl(tracking_number)
    result["carrier"] = "dhl_de"
    result["tracking_url"] = (
        f"https://www.dhl.de/de/privatkunden/dhl-sendungsverfolgung.html?piececode={tracking_number}"
    )
    return result


SCRAPER_MAP = {
    "bpost": scrape_bpost,
    "postnl": scrape_postnl,
    "dhl": scrape_dhl,
    "dhl_de": scrape_dhl_de,
    "dpd": scrape_dpd,
    "ups": scrape_ups,
    "tnt": scrape_tnt,
}


def get_tracking_info(tracking_number: str, carrier: str = "auto") -> dict:
    """Main entry point: detect carrier if needed, then scrape."""
    if not tracking_number or not tracking_number.strip():
        return {"status": "unknown", "status_detail": "No tracking number", "carrier": carrier}

    if carrier == "auto":
        carrier = detect_carrier(tracking_number)

    scraper = SCRAPER_MAP.get(carrier)
    if scraper:
        return scraper(tracking_number)

    return {
        "status": "unknown",
        "status_detail": f"Unsupported carrier: {carrier}",
        "carrier": carrier,
        "tracking_number": tracking_number,
        "tracking_url": "",
    }
