# Generated by Django 5.1.7 on 2025-06-19 11:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0034_alter_cartitem_unique_together_cartitem_variant_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='viewed',
            field=models.BooleanField(default=False, verbose_name='Baxdım'),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='MContact.productvariant'),
        ),
    ]
