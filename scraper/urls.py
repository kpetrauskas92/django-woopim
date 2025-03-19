from django.urls import path
from .views import sync_rv_orders, view_sync_log, cancel_sync_view

urlpatterns = [
    path("sync-rv-orders/", sync_rv_orders, name="sync_rv_orders"),
    path("view-sync-log/", view_sync_log, name="view_sync_log"),
    path("cancel-sync/", cancel_sync_view, name="cancel-sync"),
]