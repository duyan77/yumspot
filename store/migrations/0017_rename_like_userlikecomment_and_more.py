# Generated by Django 5.1.7 on 2025-05-17 09:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_food_description'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Like',
            new_name='UserLikeComment',
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together={('user', 'restaurant')},
        ),
        migrations.CreateModel(
            name='UserLikeRestaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.restaurant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'restaurant')},
            },
        ),
    ]
