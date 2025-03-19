from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('products/', include('products.urls')),
    path('profiles/', include('profiles.urls')),
    path('orders/', include('orders.urls')),
    path("scraper/", include("scraper.urls")),

    # Redirect root URL to dashboard (or change to 'products/' if preferred)
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]
