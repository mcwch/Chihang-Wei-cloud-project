PRODUCT_ICONS = {
    "Wireless Headphones": "\U0001F3A7",
    "USB-C Charger": "\U0001F50C",
    "Laptop Stand": "\U0001F4BB",
    "Wireless Mouse": "\U0001F5B1",
    "Mechanical Keyboard": "\u2328",
    "Portable SSD": "\U0001F4BE",
    "USB-C Hub": "\U0001F517",
    "HD Webcam": "\U0001F4F7",
    "Bluetooth Speaker": "\U0001F50A",
    "LED Desk Lamp": "\U0001F4A1",
}


CATEGORY_ICONS = {
    "audio": "\U0001F50A",
    "storage": "\U0001F4BE",
    "connectivity": "\U0001F517",
    "power": "\U0001F50C",
    "video": "\U0001F4F7",
    "workspace": "\U0001F4BB",
    "accessories": "\u2699",
}


DEFAULT_PRODUCT_ICON = "\u2699"


def get_product_icon(product_name, category):
    normalized_name = (product_name or "").strip()
    normalized_category = (category or "").strip().lower()

    if normalized_name in PRODUCT_ICONS:
        return PRODUCT_ICONS[normalized_name]

    return CATEGORY_ICONS.get(
        normalized_category,
        DEFAULT_PRODUCT_ICON,
    )
