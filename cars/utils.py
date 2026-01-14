from decimal import Decimal

# Exchange Rates (Base is KES)
EXCHANGE_RATES = {
    'KES': Decimal('1.0'),
    'USD': Decimal('0.0076'),  # Approx: 1 USD = 131 KES
    'GBP': Decimal('0.0060'),  # Approx: 1 GBP = 166 KES
    'EUR': Decimal('0.0070'),  # Approx: 1 EUR = 142 KES
    'AED': Decimal('0.0280'),  # Approx: 1 AED = 35 KES
}

CURRENCY_SYMBOLS = {
    'KES': 'KES',
    'USD': '$',
    'GBP': '£',
    'EUR': '€',
    'AED': 'AED',
}

def convert_price(amount_in_kes, target_currency):
    """
    Converts KES amount to target currency.
    """
    if not amount_in_kes:
        return 0
    
    rate = EXCHANGE_RATES.get(target_currency, Decimal('1.0'))
    converted = Decimal(amount_in_kes) * rate
    
    # Round nicely: No cents for large car prices
    return int(converted)