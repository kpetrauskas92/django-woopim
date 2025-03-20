import time
import datetime
from woocommerce import API
from django.conf import settings
from orders.models import Order, OrderItem
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.http import require_POST


def sync_woocommerce_orders(request):
    """
    Sync only WooCommerce orders from the last month.
    """
    print("🔄 Starting WooCommerce order sync...")

    wcapi = API(
        url=settings.WOOCOMMERCE_URL,
        consumer_key=settings.WOOCOMMERCE_CONSUMER_KEY,
        consumer_secret=settings.WOOCOMMERCE_CONSUMER_SECRET,
        version="wc/v3"
    )

    per_page = 10  # ✅ Increased to 20 orders per request
    page = 1
    new_orders = 0

    # ✅ Calculate the date one month ago from today
    one_month_ago = now() - datetime.timedelta(days=1)
    one_month_ago_str = one_month_ago.strftime("%Y-%m-%dT%H:%M:%S")

    while True:
        response = wcapi.get(f"orders?page={page}&per_page={per_page}&after={one_month_ago_str}").json()

        if not response:
            break  # ✅ Stop if no more orders are found

        for order in response:
            customer_name = order.get("billing", {}).get("first_name", "") + " " + order.get("billing", {}).get("last_name", "")
            order_status = order.get("status", "pending")
            total_price = order.get("total", "0.00")
            order_date = order.get("date_created", datetime.datetime.now().isoformat())

            shipping_method = ""
            shipping_cost = 0.00
            if order.get("shipping_lines"):
                shipping_method = order["shipping_lines"][0].get("method_title", "")
                shipping_cost = float(order["shipping_lines"][0].get("total", "0.00"))

            obj, created = Order.objects.update_or_create(
                order_id=order["id"],
                defaults={
                    "customer_name": customer_name.strip() or "Guest",
                    "total_price": total_price,
                    "shipping_method": shipping_method,
                    "shipping_cost": shipping_cost,
                    "order_date": order_date,
                    "status": order_status,
                }
            )

            if created:
                new_orders += 1

            print(f"✅ {'Created' if created else 'Updated'} Order {obj.order_id} - {obj.customer_name}")

            OrderItem.objects.filter(order=obj).delete()
            for item in order.get("line_items", []):
                OrderItem.objects.create(
                    order=obj,
                    product_name=item.get("name", "Unknown Product"),
                    quantity=item.get("quantity", 1),
                    price=item.get("price", "0.00"),
                )

        page += 1
        time.sleep(15)  # ✅ Prevent overloading the API

    print(f"✅ WooCommerce sync complete! {new_orders} new orders added.")
    return JsonResponse({"message": f"✅ Sync complete! {new_orders} new orders.", "status": "success"})