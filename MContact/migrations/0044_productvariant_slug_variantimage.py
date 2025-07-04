# Generated by Django 5.1.7 on 2025-07-05 08:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0043_remove_product_categories_product_subcategories'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='slug',
            field=models.SlugField(
                max_length=255, unique=False, null=True, blank=True, verbose_name='Slug'),
        ),
        migrations.CreateModel(
            name='VariantImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='variants/')),
                ('is_main', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='images', to='MContact.productvariant', verbose_name='Variant şəkli')),
            ],
            options={
                'verbose_name': 'Variant Şəkli',
                'verbose_name_plural': 'Variant Şəkilləri',
                'ordering': ['-created_at'],
            },
        ),
    ]
