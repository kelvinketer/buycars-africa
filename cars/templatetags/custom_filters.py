from django import template
from django.template.defaultfilters import slugify

register = template.Library()

@register.filter
def brand_slug(value):
    """
    Converts 'Land Rover' -> 'land-rover'
    Converts 'HONDA' -> 'honda'
    Converts 'Mercedes-Benz' -> 'mercedes-benz'
    """
    return slugify(value)

@register.filter
def whatsapp_format(value):
    """
    Formats a phone number for WhatsApp API.
    Input: 0712 345 678 or +254 712...
    Output: 254712345678
    """
    if not value:
        return ""
    
    # Convert to string and clean cleanup
    value = str(value).strip().replace(" ", "").replace("-", "").replace("+", "")
    
    # If it starts with 0 (e.g., 0712...), replace 0 with 254
    if value.startswith("0"):
        return "254" + value[1:]
        
    return value