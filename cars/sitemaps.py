from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Car

class StaticViewSitemap(Sitemap):
    """
    Maps the main static pages.
    UPDATED: Now includes Financing, Partners, and Impact pages.
    """
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # The named URLs we want Google to index
        return [
            'home', 
            'diaspora_landing', 
            'financing_page',     # NEW: B2C Funnel
            'partners_page',      # NEW: B2B Funnel
            'impact_hub',         # NEW: ESG Page
            'dealership_network', # NEW: Directory
            'brands_list', 
            'sell_page'
        ]

    def location(self, item):
        return reverse(item)

class CarSitemap(Sitemap):
    """
    Maps every single AVAILABLE car in the database.
    """
    priority = 1.0  # High priority for inventory
    changefreq = 'daily'

    def items(self):
        # Only list cars that are AVAILABLE and order by newest
        return Car.objects.filter(status='AVAILABLE').order_by('-created_at')

    def lastmod(self, obj):
        # Switched to 'created_at' because we are 100% sure this field exists
        return obj.created_at