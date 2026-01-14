from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from decimal import Decimal

# --- 1. PDF GENERATION LOGIC ---
def render_to_pdf(template_src, context_dict={}):
    """
    Helper function to generate PDF from a template.
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return result.getvalue()
    return None

# --- 2. CURRENCY CONVERSION LOGIC ---

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