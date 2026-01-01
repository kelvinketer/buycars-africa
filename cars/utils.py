from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    
    # FIX 1: Use "UTF-8" instead of "ISO-8859-1" to handle special characters (like •)
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        # FIX 2: Return raw bytes (result.getvalue()), NOT an HttpResponse.
        # The view (views.py) wraps this in an HttpResponse with the correct filename headers.
        return result.getvalue()
        
    return None