from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

# Approximate Exchange Rates (Base: 1 KES)
# You can update these later or connect to a live API
RATES = {
    'KES': 1.0,
    'UGX': 28.5,  # 1 KES = 28.5 UGX
    'TZS': 19.8,  # 1 KES = 19.8 TZS
    'RWF': 9.2,   # 1 KES = 9.2 RWF
    'USD': 0.0076, # 1 KES = 0.0076 USD
    'GBP': 0.0060, # 1 KES = 0.0060 GBP
    'AED': 0.028,  # 1 KES = 0.028 AED
    'ZAR': 0.14,   # 1 KES = 0.14 ZAR
}

@register.simple_tag(takes_context=True)
def convert_price(context, price, listing_currency):
    """
    Converts the car price from its listing currency to the user's session currency.
    """
    request = context.get('request')
    
    # 1. Get User's Preferred Currency (Default to listing currency if not set)
    if request and 'currency' in request.session:
        target_currency = request.session['currency']
    else:
        return f"{listing_currency} {intcomma(int(price))}"

    # 2. If currencies match, just return the original
    if listing_currency == target_currency:
        return f"{listing_currency} {intcomma(int(price))}"

    # 3. Perform Conversion
    try:
        # Convert original price to KES first (Base)
        # Formula: Price / Rate_of_Listing_Currency = Price_in_KES
        # Note: This assumes listing_currency is in the RATES dict. 
        # For simplicity, we assume the input price is KES for now as mostly Kenyan cars.
        # If your cars are mixed, we need a two-step conversion (From X to KES, then KES to Y).
        
        base_price_in_kes = float(price) # Assuming car price is stored in KES for the MVP
        
        # If the car itself was listed in USD, we'd need to handle that. 
        # For now, let's assume your database prices are normalized to KES or handle the conversion:
        if listing_currency != 'KES':
            # Convert TO KES first
            base_price_in_kes = float(price) / RATES.get(listing_currency, 1)

        # Convert FROM KES to Target
        rate = RATES.get(target_currency, 1)
        final_value = base_price_in_kes * rate
        
        return f"{target_currency} {intcomma(int(final_value))}"

    except (ValueError, TypeError):
        return f"{listing_currency} {price}"