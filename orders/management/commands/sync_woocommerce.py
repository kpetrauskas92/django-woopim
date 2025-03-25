import os
import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now, make_aware

from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Sync WooCommerce orders from the last few days"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Starting WooCommerce order sync...")

        per_page = 10
        page = 1
        new_orders = 0
        days_back = 5  # 🔁 Change as needed

        from_date = now() - datetime.timedelta(days=days_back)
        from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")

        def safe_get(endpoint, retries=3, delay=5):
            url = f"{settings.WOOCOMMERCE_URL}/wp-json/wc/v3/{endpoint}"
            auth = HTTPBasicAuth(settings.WOOCOMMERCE_CONSUMER_KEY, settings.WOOCOMMERCE_CONSUMER_SECRET)

            for attempt in range(retries):
                try:
                    response = requests.get(url, auth=auth, timeout=30)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.RequestException as e:
                    self.stdout.write(f"⏳ Retry {attempt+1}/{retries}: {e}")
                    time.sleep(delay)
            raise RuntimeError("❌ Failed to fetch from WooCommerce after multiple attempts.")

        while True:
            response = safe_get(f"orders?page={page}&per_page={per_page}&after={from_date_str}")

            if not response:
                break

            for order in response:
                customer_name = (
                    order.get("billing", {}).get("first_name", "") + " " +
                    order.get("billing", {}).get("last_name", "")
                ).strip() or "Guest"

                order_status = order.get("status", "pending")
                total_price = order.get("total", "0.00")
                order_date_str = order.get("date_created", datetime.datetime.now().isoformat())
                order_date = make_aware(datetime.datetime.fromisoformat(order_date_str.replace("Z", "+00:00")))

                shipping_method = ""
                shipping_cost = 0.00
                if order.get("shipping_lines"):
                    shipping_method = order["shipping_lines"][0].get("method_title", "")
                    shipping_cost = float(order["shipping_lines"][0].get("total", "0.00"))

                obj, created = Order.objects.update_or_create(
                    order_id=order["id"],
                    defaults={
                        "customer_name": customer_name,
                        "total_price": total_price,
                        "shipping_method": shipping_method,
                        "shipping_cost": shipping_cost,
                        "order_date": order_date,
                        "status": order_status,
                    }
                )

                if created:
                    new_orders += 1

                self.stdout.write(f"✅ {'Created' if created else 'Updated'} Order {obj.order_id} - {obj.customer_name}")

                OrderItem.objects.filter(order=obj).delete()
                for item in order.get("line_items", []):
                    OrderItem.objects.create(
                        order=obj,
                        product_name=item.get("name", "Unknown Product"),
                        quantity=item.get("quantity", 1),
                        price=item.get("price", "0.00"),
                    )

            page += 1
            time.sleep(10)

        self.stdout.write(f"✅ WooCommerce sync complete! {new_orders} new orders added.")
