# Generated by Django 4.1.2 on 2022-12-04 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authors', '0006_remove_author_author_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='profile_image',
            field=models.TextField(blank=True, default=''),
        ),
    ]
