from django.urls import path
from .views import product_list, product_detail

urlpatterns = [
    path('', product_list, name='product_list'),  # This means "/products/" will show the product list
    path('<int:woo_id>/', product_detail, name='product_detail'),  # "/products/<id>/" for details
]
