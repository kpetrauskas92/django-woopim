# Generated by Django 5.1.6 on 2025-02-17 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_remove_product_last_updated_product_product_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='special_offers',
        ),
        migrations.AddField(
            model_name='product',
            name='attributes',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='cross_sells',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='meta_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='shipping_class',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='short_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='stock_status',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='tags',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='width',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='productvariation',
            name='stock_status',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
