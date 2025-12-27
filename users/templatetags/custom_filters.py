from django import template

register = template.Library()

@register.filter
def whatsapp_format(value):
    """
    Converts phone numbers to WhatsApp international format (254...).
    Removes spaces, dashes, +, and replaces leading 0 with 254.
    """
    if not value:
        return ""
    
    # 1. Convert to string and remove all spaces, dashes, and plus signs
    value = str(value).replace(" ", "").replace("-", "").replace("+", "")
    
    # 2. Check for Kenyan '07' or '01' start and replace with '254'
    if value.startswith("07") or value.startswith("01"):
        return "254" + value[1:]
        
    return value