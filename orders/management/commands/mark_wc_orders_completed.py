from django.core.management.base import BaseCommand
from orders.models import Order, RetailVistaOrder
from woocommerce import API
from django.conf import settings
import time
import requests


class Command(BaseCommand):
    help = "Marks WooCommerce orders as completed if their RetailVista status is 'Closed'"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Checking RV orders with status 'Closed'...")

        # Setup WooCommerce API
        wcapi = API(
            url=settings.WOOCOMMERCE_URL,
            consumer_key=settings.WOOCOMMERCE_CONSUMER_KEY,
            consumer_secret=settings.WOOCOMMERCE_CONSUMER_SECRET,
            version="wc/v3",
            timeout=20  # ✅ Increased timeout
        )

        closed_orders = RetailVistaOrder.objects.filter(order_status__iexact="Closed")
        updated_count = 0
        skipped_count = 0
        failed_orders = []

        for rv_order in closed_orders:
            wc_order = Order.objects.filter(order_id=rv_order.reference_code).first()

            if not wc_order:
                self.stdout.write(f"❌ No WooCommerce order found for RV order {rv_order.reference_code}")
                continue

            if wc_order.status == "completed":
                skipped_count += 1
                continue

            for attempt in range(3):  # ✅ Retry up to 3 times
                try:
                    response = wcapi.put(
                        f"orders/{wc_order.order_id}",
                        data={"status": "completed"}
                    ).json()

                    if response.get("status") == "completed":
                        wc_order.status = "completed"
                        wc_order.save()
                        updated_count += 1
                        self.stdout.write(f"✅ Marked Woo Order #{wc_order.order_id} as completed.")
                    else:
                        self.stdout.write(f"⚠️ Failed to update Woo Order #{wc_order.order_id}. Response: {response}")
                    break  # ✅ Exit retry loop if successful

                except requests.exceptions.ReadTimeout:
                    self.stderr.write(f"⏳ Timeout on Woo Order #{wc_order.order_id} (Attempt {attempt + 1}/3)")
                    time.sleep(3)  # Wait before retry
                    if attempt == 2:
                        failed_orders.append(wc_order.order_id)
                except Exception as e:
                    self.stderr.write(f"❌ Error on Woo Order #{wc_order.order_id}: {e}")
                    failed_orders.append(wc_order.order_id)
                    break  # Don't retry on other errors

        # ✅ Final Summary
        self.stdout.write("\n================== SYNC SUMMARY ==================")
        self.stdout.write(f"🔁 Orders Checked: {closed_orders.count()}")
        self.stdout.write(f"✅ Completed: {updated_count}")
        self.stdout.write(f"⏭️ Skipped (Already Completed): {skipped_count}")
        if failed_orders:
            self.stderr.write(f"❌ Failed Updates: {len(failed_orders)} → {failed_orders}")
        self.stdout.write("===================================================")
