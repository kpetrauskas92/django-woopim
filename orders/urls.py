from django.urls import path
from .views import order_list, order_detail, sync_woocommerce_orders, mark_order_complete

urlpatterns = [
    path('', order_list, name='order_list'),  # List of orders
    path('<int:order_id>/', order_detail, name='order_detail'),  # Order details
    path("sync-woocommerce-orders/", sync_woocommerce_orders, name="sync_woocommerce_orders"),
    path('orders/<int:order_id>/complete/', mark_order_complete, name='mark_order_complete'),
]