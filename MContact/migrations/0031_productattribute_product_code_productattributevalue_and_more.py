# Generated by Django 5.1.7 on 2025-06-18 18:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0030_homepagebanner'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Xüsusiyyət adı')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Məhsul Xüsusiyyəti',
                'verbose_name_plural': 'Məhsul Xüsusiyyətləri',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='code',
            field=models.CharField(blank=True, help_text='Əl ilə daxil edilir; təkrarlanma məhdudiyyəti yoxdur', max_length=50, verbose_name='Məhsul kodu'),
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100, verbose_name='Dəyər')),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='MContact.productattribute', verbose_name='Xüsusiyyət')),
            ],
            options={
                'verbose_name': 'Xüsusiyyət Dəyəri',
                'verbose_name_plural': 'Xüsusiyyət Dəyərləri',
                'ordering': ['attribute__name', 'value'],
                'unique_together': {('attribute', 'value')},
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, help_text='Əl ilə daxil olunur; təkrarlanma qadağası yoxdur', max_length=50, verbose_name='Versiya kodu')),
                ('price_override', models.DecimalField(blank=True, decimal_places=2, help_text='Boş saxlasanız əsas məhsul qiyməti qəbul edilir', max_digits=10, null=True, verbose_name='Alternativ qiymət')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktiv')),
                ('attribute_values', models.ManyToManyField(related_name='product_variants', to='MContact.productattributevalue', verbose_name='Xüsusiyyət dəyərləri')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='MContact.product', verbose_name='Məhsul')),
            ],
            options={
                'verbose_name': 'Məhsul Versiyası',
                'verbose_name_plural': 'Məhsul Versiyaları',
                'ordering': ['product', 'id'],
            },
        ),
    ]
