# Generated by Django 5.1.7 on 2025-06-07 11:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0016_userdevicetoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='blogs/', verbose_name='Blog şəkli')),
                ('is_main', models.BooleanField(default=False, verbose_name='Əsas şəkil')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yüklənmə tarixi')),
                ('blog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='MContact.blog', verbose_name='Blog')),
            ],
            options={
                'verbose_name': 'Blog Şəkli',
                'verbose_name_plural': 'Blog Şəkilləri',
                'ordering': ['-created_at'],
            },
        ),
    ]
