# Generated by Django 5.1.7 on 2025-07-01 19:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0041_category_subcategories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='subcategories',
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Alt kateqoriya adı')),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True, verbose_name='Slug')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaradılma tarixi')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='MContact.category', verbose_name='Alt kateqoriya')),
            ],
            options={
                'verbose_name': 'Alt kateqoriya',
                'verbose_name_plural': 'Alt kateqoriyalar',
                'ordering': ['name'],
                'unique_together': {('category', 'name')},
            },
        ),
    ]
