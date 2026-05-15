"""Constants for Parcel Tracker integration."""

DOMAIN = "parcel_tracker"
PLATFORM = "sensor"

CONF_TRACKING_NUMBER = "tracking_number"
CONF_CARRIER = "carrier"
CONF_FRIENDLY_NAME = "friendly_name"

DEFAULT_SCAN_INTERVAL = 30  # minutes
MAX_PARCELS = 10

CARRIERS = {
    "auto": "Auto-detect",
    "bpost": "bPost",
    "dhl": "DHL",
    "tnt": "TNT / FedEx",
    "ups": "UPS",
    "postnl": "PostNL",
}

TRACKING_URLS = {
    "bpost": "https://track.bpost.cloud/btr/web/#/search?itemCode={tracking_number}&lang=nl",
    "dhl": "https://www.dhl.com/be-nl/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    "tnt": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    "ups": "https://www.ups.com/track?loc=nl_BE&tracknum={tracking_number}",
    "postnl": "https://postnl.nl/tracktrace/?B={tracking_number}&P=",
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
