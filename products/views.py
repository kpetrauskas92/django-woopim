from django.shortcuts import render, get_object_or_404
from django.db import models
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
    """Convert WooCommerce values to a valid Decimal or default to 0.00."""
    try:
        if value in [None, "", "None"]:
            return decimal.Decimal("0.00")
        return decimal.Decimal(str(value))
    except decimal.InvalidOperation:
        return decimal.Decimal("0.00")

def sync_products():
    """Fetch products from WooCommerce API in batches of 15."""
    per_page = 15  
    page = 1       

    while True:
        response = wcapi.get(f"products?page={page}&per_page={per_page}").json()

        if not response:  # If no more products, stop the loop
            print("✅ Product sync completed.")
            break

        for p in response:
            try:
                product_type = p.get("type", "simple")
                special_offers = any(category["name"] == "Special Offers" for category in p.get("categories", []))

                # Safely convert prices
                full_price = safe_decimal(p.get("regular_price", "0.00"))
                sale_price = safe_decimal(p.get("sale_price", "0.00"))

                # Create or update product
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
                        "shipping_class": p.get("shipping_class", ""),
                        "special_offers": special_offers,  # Update the special offers field
                    }
                )

                # Handle variations for variable products
                if product_type == "variable":
                    variations = wcapi.get(f"products/{p['id']}/variations").json()

                    for v in variations:
                        try:
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
                        except Exception as ve:
                            print(f"⚠️ Failed to sync variation {v['id']}: {ve}")

            except Exception as e:
                print(f"❌ Error syncing product {p['id']}: {e}")

        print(f"✅ Synced {len(response)} products from page {page}")
        page += 1  
        time.sleep(60)  # Wait 1 minute before fetching the next batch




def product_list(request):
    """Display product list with search and filtering."""
    query = Product.objects.all()

    # 🔍 Search by name, SKU, or ID
    search_query = request.GET.get('search')
    if search_query:
        query = query.filter(
            models.Q(name__icontains=search_query) |
            models.Q(sku__icontains=search_query) |
            models.Q(woo_id__icontains=search_query)
        )

    # 📦 Filter by stock status
    stock_status = request.GET.get('stock_status')
    if stock_status:
        query = query.filter(stock_status=stock_status)

    # 🔐 Filter by product status (published/private)
    product_status = request.GET.get('product_status')
    if product_status:
        query = query.filter(status=product_status)

    # 🏷️ Filter by special offers
    special_offers = request.GET.get('special_offers')
    if special_offers == 'yes':
        query = query.filter(special_offers=True)
    elif special_offers == 'no':
        query = query.filter(special_offers=False)

    # 📂 Filter by category
    category = request.GET.get('category')
    if category:
        query = query.filter(categories__icontains=category)

    # Get unique categories for the dropdown
    categories = Product.objects.values_list('categories', flat=True).distinct()

    context = {
        'products': query,
        'categories': categories,
    }

    return render(request, 'product_list.html', context)

def product_detail(request, woo_id):
    """Display full product details like WooCommerce."""
    product = get_object_or_404(Product, woo_id=woo_id)
    return render(request, "product_detail.html", {"product": product})
