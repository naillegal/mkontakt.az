# Generated by Django 5.1.7 on 2025-06-19 12:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0037_alter_cartitem_variant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productattribute',
            name='name_az',
        ),
        migrations.RemoveField(
            model_name='productattribute',
            name='name_en',
        ),
        migrations.RemoveField(
            model_name='productattribute',
            name='name_ru',
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='value_az',
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='value_en',
        ),
        migrations.RemoveField(
            model_name='productattributevalue',
            name='value_ru',
        ),
    ]
