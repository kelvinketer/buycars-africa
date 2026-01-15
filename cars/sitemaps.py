from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Car

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        # The named URLs we want Google to index
        return ['home', 'diaspora_landing', 'sell_page', 'brands_list', 'select_account']

    def location(self, item):
        return reverse(item)

class CarSitemap(Sitemap):
    priority = 1.0  # High priority for inventory
    changefreq = 'weekly'

    def items(self):
        # Only list cars that are AVAILABLE
        return Car.objects.filter(status='AVAILABLE')

    def lastmod(self, obj):
        return obj.updated_at