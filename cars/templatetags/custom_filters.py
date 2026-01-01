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