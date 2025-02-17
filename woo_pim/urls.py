from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('products/', include('products.urls')),

    # Redirect "/" to "/products/"
    path('', lambda request: redirect('/products/', permanent=True)),
]
