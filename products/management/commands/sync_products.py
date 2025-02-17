from django.core.management.base import BaseCommand
from products.views import sync_products

class Command(BaseCommand):
    help = "Sync WooCommerce products in batches of 15 every minute"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting product sync..."))
        sync_products()
        self.stdout.write(self.style.SUCCESS("Product sync completed!"))
