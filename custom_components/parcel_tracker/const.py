"""Constants for Parcel Tracker integration."""

DOMAIN = "parcel_tracker"
VERSION = "1.13.0"
PLATFORM = "sensor"

CONF_TRACKING_NUMBER = "tracking_number"
CONF_CARRIER = "carrier"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_DHL_API_KEY = "dhl_api_key"
CONF_17TRACK_API_KEY = "seventeentrack_api_key"
CONF_POSTAL_CODE = "postal_code"

DEFAULT_SCAN_INTERVAL = 30  # minutes
MAX_PARCELS = 10

CARRIERS = {
    "auto": "Auto-detect",
    "bpost": "bPost",
    "dhl": "DHL (Internationaal)",
    "dhl_de": "DHL Germany",
    "dpd": "DPD",
    "fourpx": "4PX / China Post",
    "tnt": "TNT / FedEx",
    "ups": "UPS",
    "postnl": "PostNL",
    "colisprive": "Colis Privé (experimenteel)",
    "gls": "GLS (via 17track)",
    "mondialrelay": "Mondial Relay (via 17track)",
}

TRACKING_URLS = {
    "bpost": "https://track.bpost.cloud/btr/web/#/search?itemCode={tracking_number}&lang=nl",
    "dhl": "https://www.dhl.com/be-nl/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    "dhl_de": "https://www.dhl.de/de/privatkunden/dhl-sendungsverfolgung.html?piececode={tracking_number}",
    "dpd": "https://www.dpdgroup.com/be/mydpd/my-parcels/track?lang=nl&parcelNumber={tracking_number}",
    "fourpx": "https://track.4px.com/#/result/0/{tracking_number}",
    "tnt": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    "ups": "https://www.ups.com/track?loc=nl_BE&tracknum={tracking_number}",
    "postnl": "https://postnl.nl/tracktrace/?B={tracking_number}&P=",
    "colisprive": "https://colisprive.com/moncolis/pages/detailColis.aspx?numColis={tracking_number}&lang=NL",
    "gls": "https://gls-group.eu/BE/nl/pakket-volgen?match={tracking_number}",
    "mondialrelay": "https://www.mondialrelay.fr/suivi-de-colis?numeroExpedition={tracking_number}",
}

STATUS_DELIVERED = "delivered"
STATUS_IN_TRANSIT = "in_transit"
STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
STATUS_PENDING = "pending"
STATUS_EXCEPTION = "exception"
STATUS_UNKNOWN = "unknown"

STATUS_ICONS = {
    "delivered": "mdi:package-variant-closed-check",
    "in_transit": "mdi:truck-delivery",
    "out_for_delivery": "mdi:truck-fast",
    "pending": "mdi:clock-outline",
    "exception": "mdi:alert-circle",
    "unknown": "mdi:package-variant",
}
