# Generated by Django 5.1.6 on 2025-02-19 11:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_remove_product_special_offers_product_attributes_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='height',
        ),
        migrations.RemoveField(
            model_name='product',
            name='length',
        ),
        migrations.RemoveField(
            model_name='product',
            name='weight',
        ),
        migrations.RemoveField(
            model_name='product',
            name='width',
        ),
    ]
