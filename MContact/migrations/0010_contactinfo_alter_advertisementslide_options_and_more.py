# Generated by Django 5.1.7 on 2025-04-13 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MContact', '0009_contactmessage_alter_blog_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('technical_email', models.EmailField(max_length=254, verbose_name='Texniki Email')),
                ('technical_mobile', models.CharField(max_length=50, verbose_name='Texniki Mobil')),
                ('support_email', models.EmailField(max_length=254, verbose_name='Dəstək Email')),
                ('support_mobile', models.CharField(max_length=50, verbose_name='Dəstək Mobil')),
                ('instagram', models.URLField(blank=True, null=True, verbose_name='Instagram')),
                ('facebook', models.URLField(blank=True, null=True, verbose_name='Facebook')),
                ('whatsapp', models.URLField(blank=True, null=True, verbose_name='WhatsApp')),
                ('youtube', models.URLField(blank=True, null=True, verbose_name='YouTube')),
            ],
            options={
                'verbose_name': 'Əlaqə Məlumatı',
                'verbose_name_plural': 'Əlaqə Məlumatları',
            },
        ),
        migrations.AlterModelOptions(
            name='advertisementslide',
            options={'ordering': ['created_at'], 'verbose_name': 'Reklam slayderi', 'verbose_name_plural': 'Reklam slayderləri'},
        ),
        migrations.AlterModelOptions(
            name='partnerslider',
            options={'ordering': ['created_at'], 'verbose_name': 'Partnyor slayderi', 'verbose_name_plural': 'Partnyor slayderləri'},
        ),
    ]
