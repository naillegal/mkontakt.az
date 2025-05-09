# Generated by Django 5.1.7 on 2025-04-20 09:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0011_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wish',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wished_by', to='MContact.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishes', to='MContact.user')),
            ],
            options={
                'verbose_name': 'Wishlist Sətiri',
                'verbose_name_plural': 'Wishlist',
                'unique_together': {('user', 'product')},
            },
        ),
    ]
