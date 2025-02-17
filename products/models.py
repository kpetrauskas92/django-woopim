from django.db import models

class Product(models.Model):
    woo_id = models.IntegerField(unique=True)  # WooCommerce Product ID
    sku = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)
    full_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(null=True, blank=True)  # Only used for simple products
    stock_status = models.CharField(max_length=20, blank=True, null=True)  # in_stock / out_of_stock
    status = models.CharField(max_length=20, choices=[('publish', 'Published'), ('private', 'Private'), ('draft', 'Draft')])
    product_type = models.CharField(max_length=20, choices=[('simple', 'Simple'), ('variable', 'Variable')], default='simple')
    permalink = models.URLField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    categories = models.JSONField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    meta_data = models.JSONField(blank=True, null=True)
    attributes = models.JSONField(blank=True, null=True)  # General attributes for variable products
    cross_sells = models.JSONField(blank=True, null=True)  # Store linked products

    # Weight, Dimensions & Shipping Class
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_class = models.CharField(max_length=255, blank=True, null=True)

    def discount_percentage(self):
        """Calculate discount percentage if there is a sale."""
        if self.sale_price and self.full_price and self.sale_price < self.full_price:
            return round(100 - (self.sale_price / self.full_price * 100), 2)
        return None

    def __str__(self):
        return self.name


class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name="variations", on_delete=models.CASCADE)
    variation_id = models.IntegerField(unique=True)  # WooCommerce Variation ID
    sku = models.CharField(max_length=100, blank=True, null=True)
    full_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(null=True, blank=True)
    stock_status = models.CharField(max_length=20, blank=True, null=True)  # in_stock / out_of_stock
    attributes = models.JSONField()  # Stores variation attributes (size, color, etc.)

    def discount_percentage(self):
        """Calculate discount percentage for variations."""
        if self.sale_price and self.full_price and self.sale_price < self.full_price:
            return round(100 - (self.sale_price / self.full_price * 100), 2)
        return None

    def __str__(self):
        return f"{self.product.name} - {self.sku or 'No SKU'}"
