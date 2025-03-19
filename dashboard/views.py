from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from products.models import Product, EditRequest, NewProductRequest
from django.utils.timezone import now, timedelta

@login_required
def index(request):
    """Dashboard showing product analytics and user insights."""

    # Calculate weekly range
    start_of_week = now() - timedelta(days=7)

    # Product Insights
    total_products = Product.objects.count()
    on_sale = Product.objects.filter(sale_price__gt=0).count()
    out_of_stock = Product.objects.filter(stock_quantity=0).count()
    special_offers = Product.objects.filter(categories__icontains='Special Offers').count()

    # Weekly Insights
    new_products = Product.objects.filter(created_at__gte=start_of_week).count()
    new_edit_requests = EditRequest.objects.filter(created_at__gte=start_of_week, status="pending").count()
    new_product_requests = NewProductRequest.objects.filter(created_at__gte=start_of_week, status="pending").count()

    context = {
        "total_products": total_products,
        "on_sale": on_sale,
        "out_of_stock": out_of_stock,
        "special_offers": special_offers,
        "new_products": new_products,
        "new_edit_requests": new_edit_requests,
        "new_product_requests": new_product_requests,
    }

    return render(request, 'dashboard/index.html', context)
