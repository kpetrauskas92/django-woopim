from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, RetailVistaOrder
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .utils import sync_woocommerce_orders
from datetime import timedelta
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.conf import settings
from woocommerce import API


@login_required
def order_list(request):
    sort_by = request.GET.get("sort", "-order_date")
    filter_status = request.GET.get("status", "")
    rv_status = request.GET.get("rv_status", "")
    page = request.GET.get("page", 1)

    orders = Order.objects.all()

    if filter_status:
        orders = orders.filter(status=filter_status)

    orders = orders.order_by(sort_by)
    orders = list(orders)  # evaluate queryset

    # Enrich orders with RV data
    flagged_orders = []
    two_weeks_ago = now() - timedelta(weeks=2)
    for order in orders:
        rv_order = order.get_rv_order()
        order.rv_synced = order.is_synced_with_rv()
        order.rv_order_status = rv_order.order_status if rv_order else None
        order.rv_canceled = rv_order.canceled_status if rv_order else None
        order.rv_last_synced = rv_order.last_synced if rv_order else None

        # Flag orders not RV closed and older than 2 weeks
        if (order.rv_order_status != "closed") and (order.order_date < two_weeks_ago):
            flagged_orders.append(order)

    if rv_status:
        orders = [order for order in orders if (order.rv_order_status or "").lower() == rv_status.lower()]

    paginator = Paginator(orders, 20)
    paginated_orders = paginator.get_page(page)

    status_counts = {
        "pending": Order.objects.filter(status="pending").count(),
        "processing": Order.objects.filter(status="processing").count(),
        "completed": Order.objects.filter(status="completed").count(),
        "cancelled": Order.objects.filter(status="cancelled").count(),
        "refunded": Order.objects.filter(status="refunded").count(),
        "failed": Order.objects.filter(status="failed").count(),
        "on_hold": Order.objects.filter(status="on-hold").count(),
    }

    return render(request, 'order_list.html', {
        "orders": paginated_orders,
        "sort_by": sort_by,
        "filter_status": filter_status,
        "rv_status": rv_status,
        "status_counts": status_counts,
        "flagged_orders": flagged_orders[:5],  # show top 5 critical ones
    })


def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    
    # Fetch the matching RetailVistaOrder
    rv_order = RetailVistaOrder.objects.filter(reference_code=order.order_id).first()

    return render(request, 'order_detail.html', {
        'order': order,
        'rv_order': rv_order,  # Pass RV order data to template
    })


@csrf_exempt  # Temporary workaround (NOT recommended for production)
def sync_woocommerce_orders_view(request):
    """
    Triggers the WooCommerce order sync process.
    """
    if request.method == "POST":
        try:
            result = sync_woocommerce_orders()  # ✅ Call WITHOUT passing request
            return JsonResponse({"message": result["message"], "status": "success"})
        except Exception as e:
            return JsonResponse({"message": f"❌ Sync Failed! Error: {str(e)}", "status": "error"})

    return JsonResponse({"error": "Invalid request method."}, status=400)


@require_POST
def mark_order_complete(request, order_id):
    """
    Mark an order as complete.
    """
    order = get_object_or_404(Order, order_id=order_id)
    
    # Check if the order is already completed
    if order.status == "completed":
        message = f"Order {order.order_id} is already marked as complete."
    else:
        # Mark the order as completed locally
        order.status = "completed"
        order.save()
        message = f"Order {order.order_id} marked as complete."
        
        # OPTIONAL: Update the WooCommerce order via the WooCommerce REST API.
        # Uncomment and configure the code below with your WooCommerce site details.
        #
        wcapi = API(
            url=settings.WOOCOMMERCE_URL,
            consumer_key=settings.WOOCOMMERCE_CONSUMER_KEY,
            consumer_secret=settings.WOOCOMMERCE_CONSUMER_SECRET,
            version="wc/v3"
        )
        data = {"status": "completed"}
        response = wcapi.put(f"orders/{order_id}", data)
        if response.status_code != 200:
            message = f"Local update succeeded, but failed to update WooCommerce."
    
    # For HTMX requests, return a partial that will update the modal content.
    if request.headers.get('HX-Request'):
        return render(request, "includes/order_status.html", {"order": order, "message": message})
    
    # Fallback for non-HTMX AJAX requests.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"message": message, "status": "success"})
    
    # Otherwise, do a full redirect.
    return redirect('order_detail', order_id=order.order_id)