from django.db import models

class RetailVistaOrder(models.Model):
    reference_code = models.CharField(max_length=50, unique=True)  # Unique order identifier
    customer = models.CharField(max_length=255)
    transport_type = models.CharField(max_length=255)
    order_status = models.CharField(max_length=50)
    canceled_status = models.CharField(max_length=10, choices=[("Yes", "Yes"), ("No", "No")])

    last_checked = models.DateTimeField(auto_now=True)  # Auto-updates when modified

    def __str__(self):
        return f"{self.reference_code} - {self.customer}"