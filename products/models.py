from django.db import models
from django.utils.timezone import now


# 🌟 Product Model
class Product(models.Model):
    woo_id = models.IntegerField(unique=True)  # WooCommerce Product ID
    sku = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)
    full_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    special_offers = models.BooleanField(default=False)
    stock_quantity = models.IntegerField(null=True, blank=True)
    stock_status = models.CharField(max_length=20, blank=True, null=True)  # instock / outofstock
    status = models.CharField(max_length=20, choices=[('publish', 'Published'), ('private', 'Private'), ('draft', 'Draft')])
    product_type = models.CharField(max_length=20, choices=[('simple', 'Simple'), ('variable', 'Variable')], default='simple')
    permalink = models.URLField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    categories = models.JSONField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    meta_data = models.JSONField(blank=True, null=True)
    attributes = models.JSONField(blank=True, null=True)
    cross_sells = models.JSONField(blank=True, null=True)

    shipping_class = models.CharField(max_length=255, blank=True, null=True)

    # 🌟 Timestamps
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    updated_at = models.DateTimeField(auto_now=True)      # Automatically updated on save

    def discount_percentage(self):
        """Calculate discount percentage if on sale."""
        if self.sale_price and self.full_price and self.sale_price < self.full_price:
            return round(100 - (self.sale_price / self.full_price * 100), 2)
        return None

    def __str__(self):
        return self.name


# 🌟 Product Variation Model
class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name="variations", on_delete=models.CASCADE)
    variation_id = models.IntegerField(unique=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    full_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(null=True, blank=True)
    stock_status = models.CharField(max_length=20, blank=True, null=True)
    attributes = models.JSONField()  # e.g., Size, Color, etc.

    # 🌟 Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def discount_percentage(self):
        """Calculate discount percentage for variations."""
        if self.sale_price and self.full_price and self.sale_price < self.full_price:
            return round(100 - (self.sale_price / self.full_price * 100), 2)
        return None

    def __str__(self):
        return f"{self.product.name} - {self.sku or 'No SKU'}"


# 🌟 Edit Request Model
class EditRequest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='edit_requests')
    requested_by = models.CharField(max_length=100)
    changes = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)  # When request was made
    updated_at = models.DateTimeField(auto_now=True)      # When last updated

    def __str__(self):
        return f"Edit Request for {self.product.name} by {self.requested_by}"


# 🌟 New Product Request Model
class NewProductRequest(models.Model):
    requested_by = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    product_details = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('added', 'Added')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"New Product Request: {self.product_name} by {self.requested_by}"
