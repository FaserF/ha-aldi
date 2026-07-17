"""Constants for the ALDI weekly offers integration."""

DOMAIN = "aldi"
PLATFORMS = ["button", "sensor"]

# Configuration keys
CONF_REGION = "region"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 24  # hours
MIN_UPDATE_INTERVAL = 1  # hours
MAX_UPDATE_INTERVAL = 24  # hours

# Sensor attributes
ATTR_DISCOUNTS = "discounts"
ATTR_DISCOUNT_TITLE = "product"
ATTR_DISCOUNT_PRICE = "price"
ATTR_BASE_PRICE = "base_price"
ATTR_PICTURE = "picture_link"
ATTR_VALID_DATE = "valid_until"
ATTR_CATEGORY = "category"

# Region selections
REGION_SUED = "sued"
REGION_NORD = "nord"
REGION_BOTH = "both"
