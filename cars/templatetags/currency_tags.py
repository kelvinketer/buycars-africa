from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

# Approximate Exchange Rates (Base: 1 KES) - Updated for Pan-African Expansion
# NOTE: In a production environment, fetch these from an API (e.g., OpenExchangeRates)
RATES = {
    'KES': 1.0,
    
    # East Africa (EAC & Horn)
    'UGX': 28.5,   # 1 KES ~ 28.5 Uganda Shillings
    'TZS': 19.8,   # 1 KES ~ 19.8 Tanzania Shillings
    'RWF': 9.2,    # 1 KES ~ 9.2 Rwanda Francs
    'ETB': 0.95,   # 1 KES ~ 0.95 Ethiopian Birr
    
    # West Africa
    'NGN': 11.5,   # 1 KES ~ 11.5 Nigerian Naira
    'GHS': 0.12,   # 1 KES ~ 0.12 Ghanaian Cedis
    
    # North Africa
    'EGP': 0.37,   # 1 KES ~ 0.37 Egyptian Pounds
    
    # Southern Africa
    'ZAR': 0.14,   # 1 KES ~ 0.14 South African Rand
    'NAD': 0.14,   # 1 KES ~ 0.14 Namibian Dollar (Pegged to ZAR)
    'AOA': 6.5,    # 1 KES ~ 6.5 Angolan Kwanza
    
    # International Trade
    'USD': 0.0076, # 1 KES ~ 0.0076 US Dollars
    'GBP': 0.0060, # 1 KES ~ 0.0060 British Pounds
    'AED': 0.028,  # 1 KES ~ 0.028 UAE Dirhams
    'JPY': 1.15,   # 1 KES ~ 1.15 Japanese Yen
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
        base_price_in_kes = float(price) 
        
        # If the car itself was NOT listed in KES, normalize it to KES first
        if listing_currency != 'KES':
            base_rate = RATES.get(listing_currency, 1.0)
            base_price_in_kes = float(price) / base_rate

        # Convert FROM KES to Target
        target_rate = RATES.get(target_currency, 1.0)
        final_value = base_price_in_kes * target_rate
        
        return f"{target_currency} {intcomma(int(final_value))}"

    except (ValueError, TypeError):
        return f"{listing_currency} {price}"