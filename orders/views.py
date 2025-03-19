from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, RetailVistaOrder
from django.views.decorators.csrf import csrf_exempt
from .utils import sync_woocommerce_orders
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.conf import settings
from woocommerce import API


def order_list(request):
    # Get filtering and sorting parameters from the request
    sort_by = request.GET.get("sort", "-order_date")  # Default: newest first
    filter_status = request.GET.get("status", "")  # Default: no filter
    rv_status = request.GET.get("rv_status", "")  # New filter for RV Order Status

    # Fetch orders with filtering and sorting
    orders = Order.objects.all()
    
    if filter_status:  # Apply status filter if selected
        orders = orders.filter(status=filter_status)

    orders = orders.order_by(sort_by)  # Apply sorting

    # Evaluate orders to allow filtering on computed attributes
    orders = list(orders)
    
    # Get associated RetailVista orders and annotate orders
    for order in orders:
        rv_order = order.get_rv_order()
        order.rv_synced = order.is_synced_with_rv()  # True/False
        order.rv_order_status = rv_order.order_status if rv_order else None
        order.rv_canceled = rv_order.canceled_status if rv_order else None
        order.rv_last_synced = rv_order.last_synced if rv_order else None

    # Filter orders by RV Order Status if a filter is provided
    if rv_status:
        orders = [order for order in orders if (order.rv_order_status or "").lower() == rv_status.lower()]

    # Count orders by status
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
        "orders": orders,
        "sort_by": sort_by,
        "filter_status": filter_status,
        "rv_status": rv_status,  # Pass the selected RV status back to the template
        "status_counts": status_counts,
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