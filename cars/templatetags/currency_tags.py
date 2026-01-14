from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from cars.utils import convert_price, CURRENCY_SYMBOLS

register = template.Library()

@register.simple_tag(takes_context=True)
def global_price(context, price_kes):
    """
    Usage: {% global_price car.price %}
    """
    request = context['request']
    # Default to KES if no session is set
    current_currency = request.session.get('currency', 'KES')
    
    # Get the symbol
    symbol = CURRENCY_SYMBOLS.get(current_currency, 'KES')
    
    # Do the math
    new_price = convert_price(price_kes, current_currency)
    
    # Format with commas (e.g., "16,500")
    formatted_price = intcomma(new_price)
    
    return f"{symbol} {formatted_price}"