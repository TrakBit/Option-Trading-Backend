# Generated by Django 2.2.2 on 2019-08-02 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20190722_1707'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=40)),
                ('strike_price', models.FloatField(max_length=40)),
                ('profit', models.FloatField(max_length=40)),
            ],
        ),
    ]
