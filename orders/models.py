from django.db import models
from django.utils.timezone import now

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
        ('on-hold', 'On Hold'),
    ]

    order_id = models.IntegerField(unique=True)  # WooCommerce Order ID
    customer_name = models.CharField(max_length=255)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_method = models.CharField(max_length=255, blank=True, null=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_synced_with_rv(self):
        """Checks if this order matches an RV order based on order ID and customer name"""
        rv_order = RetailVistaOrder.objects.filter(reference_code=self.order_id).first()
        if rv_order:
            # Swap name format from "Last, First" → "First Last" for comparison
            rv_customer_name = " ".join(rv_order.customer_name.split(", ")[::-1]) if ", " in rv_order.customer_name else rv_order.customer_name
            return rv_customer_name.lower() == self.customer_name.lower()
        return False

    def get_rv_order(self):
        """Retrieves the associated RetailVista order"""
        return RetailVistaOrder.objects.filter(reference_code=self.order_id).first()

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"


class RetailVistaOrder(models.Model):
    order_status = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)  # Stored as "Last, First"
    transport_type = models.CharField(max_length=255)
    reference_code = models.CharField(max_length=50, unique=True)  # Matches WooCommerce Order ID
    canceled_status = models.CharField(max_length=10, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')
    last_synced = models.DateTimeField(default=now)

    def __str__(self):
        return f"RV Order {self.reference_code} - {self.customer_name}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.order.order_id})"
