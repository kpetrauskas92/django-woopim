from django.shortcuts import render, get_object_or_404
from .models import Product, ProductVariation
from woocommerce import API
from django.conf import settings
import time, decimal

wcapi = API(
    url=settings.WOOCOMMERCE_URL,
    consumer_key=settings.WOOCOMMERCE_CONSUMER_KEY,
    consumer_secret=settings.WOOCOMMERCE_CONSUMER_SECRET,
    version="wc/v3"
)


def safe_decimal(value):
    """Convert WooCommerce price values to a valid Decimal or default to 0.00."""
    try:
        return decimal.Decimal(value) if value not in [None, "", "None"] else decimal.Decimal("0.00")
    except decimal.InvalidOperation:
        return decimal.Decimal("0.00")


def sync_products():
    """Fetch products from WooCommerce API in batches of 15."""
    per_page = 15  
    page = 1       

    while True:
        response = wcapi.get(f"products?page={page}&per_page={per_page}").json()

        if not response:  # If there are no more products, stop the loop
            break

        for p in response:
            special_offers = any(category["name"] == "Special Offers" for category in p["categories"])
            product_type = p.get("type", "simple")

            # Convert prices safely using safe_decimal()
            full_price = safe_decimal(p.get("regular_price", "0.00"))
            sale_price = safe_decimal(p.get("sale_price", "0.00"))

            product, created = Product.objects.update_or_create(
                woo_id=p["id"],
                defaults={
                    "sku": p.get("sku", "") if product_type == "simple" else None,
                    "name": p["name"],
                    "image_url": p["images"][0]["src"] if p["images"] else None,
                    "full_price": full_price,
                    "sale_price": sale_price,
                    "stock_quantity": p.get("stock_quantity", 0) if product_type == "simple" else None,
                    "stock_status": p.get("stock_status", ""),
                    "status": p["status"],
                    "permalink": p["permalink"],
                    "product_type": product_type,
                    "description": p.get("description", ""),
                    "short_description": p.get("short_description", ""),
                    "categories": [c["name"] for c in p.get("categories", [])],
                    "tags": [t["name"] for t in p.get("tags", [])],
                    "meta_data": p.get("meta_data", []),
                    "attributes": p.get("attributes", []),
                    "cross_sells": [c_id for c_id in p.get("cross_sell_ids", [])],
                    "weight": p.get("weight", "0"),
                    "length": p["dimensions"]["length"] if "dimensions" in p else None,
                    "width": p["dimensions"]["width"] if "dimensions" in p else None,
                    "height": p["dimensions"]["height"] if "dimensions" in p else None,
                    "shipping_class": p.get("shipping_class", ""),
                }
            )

            # Handle variations for variable products
            if product_type == "variable":
                variations = wcapi.get(f"products/{p['id']}/variations").json()

                for v in variations:
                    var_full_price = safe_decimal(v.get("regular_price", "0.00"))
                    var_sale_price = safe_decimal(v.get("sale_price", "0.00"))

                    ProductVariation.objects.update_or_create(
                        variation_id=v["id"],
                        product=product,
                        defaults={
                            "sku": v.get("sku", ""),
                            "full_price": var_full_price,
                            "sale_price": var_sale_price,
                            "stock_quantity": v.get("stock_quantity", 0),
                            "stock_status": v.get("stock_status", ""),
                            "attributes": v.get("attributes", []),
                        }
                    )

        print(f"Synced {len(response)} products from page {page}")
        page += 1  
        time.sleep(60)  # Wait 1 minute before fetching the next batch




def product_list(request):
    """Display all products in a table."""
    products = Product.objects.all()
    return render(request, "product_list.html", {"products": products})

def product_detail(request, woo_id):
    """Display full product details like WooCommerce."""
    product = get_object_or_404(Product, woo_id=woo_id)
    return render(request, "product_detail.html", {"product": product})
