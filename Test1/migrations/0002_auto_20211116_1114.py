# Generated by Django 3.1.6 on 2021-11-16 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Test1', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stocksrecord',
            name='sold_at',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
