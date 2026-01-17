from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

# --- EXCHANGE RATES (Kept your Pan-African list) ---
# NOTE: In production, fetch these from an API (e.g., OpenExchangeRates)
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
def display_price(context, price, listing_currency='KES'):
    """
    Converts the car price from its listing currency to the user's session currency.
    Usage: {% display_price car.price 'KES' %}
    """
    # 1. Safety Check: If price is missing or 0
    if not price:
        return "Price on Request"

    request = context.get('request')
    target_currency = 'KES' # Default fallback

    # 2. Get User's Preferred Currency
    if request and 'currency' in request.session:
        target_currency = request.session['currency']

    # 3. If currencies match, return original immediately
    if listing_currency == target_currency:
        return f"{listing_currency} {intcomma(int(price))}"

    # 4. Perform Conversion
    try:
        # Step A: Normalize to KES (if car wasn't listed in KES)
        base_price_in_kes = float(price)
        if listing_currency != 'KES':
            base_rate = RATES.get(listing_currency, 1.0)
            base_price_in_kes = base_price_in_kes / base_rate

        # Step B: Convert KES to Target Currency
        target_rate = RATES.get(target_currency, 1.0)
        final_value = base_price_in_kes * target_rate
        
        # Formatting for USD/GBP/EUR (2 decimal places), others (Integers)
        if target_currency in ['USD', 'GBP', 'EUR']:
            return f"{target_currency} {intcomma(round(final_value, 2))}"
        
        return f"{target_currency} {intcomma(int(final_value))}"

    except (ValueError, TypeError):
        return f"{listing_currency} {price}"