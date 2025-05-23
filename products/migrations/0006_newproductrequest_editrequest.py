# Generated by Django 5.1.6 on 2025-02-21 17:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_product_special_offers'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewProductRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_by', models.CharField(max_length=100)),
                ('product_name', models.CharField(max_length=255)),
                ('product_details', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('added', 'Added')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='EditRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_by', models.CharField(max_length=100)),
                ('changes', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='edit_requests', to='products.product')),
            ],
        ),
    ]
