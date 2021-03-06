# Generated by Django 2.1.7 on 2019-06-16 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Expiry_Date',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upstox_date', models.CharField(max_length=40)),
                ('expiry_date', models.CharField(max_length=40)),
                ('label_date', models.CharField(max_length=40)),
                ('future_date', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Full_Quote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strike_price', models.FloatField(max_length=40)),
                ('exchange', models.CharField(max_length=40)),
                ('symbol', models.CharField(max_length=40)),
                ('ltp', models.CharField(max_length=40)),
                ('close', models.CharField(max_length=40)),
                ('open', models.CharField(max_length=40)),
                ('high', models.CharField(max_length=40)),
                ('low', models.CharField(max_length=40)),
                ('vtt', models.CharField(max_length=40)),
                ('atp', models.CharField(max_length=40)),
                ('oi', models.FloatField(max_length=40)),
                ('spot_price', models.CharField(max_length=40)),
                ('total_buy_qty', models.CharField(max_length=40)),
                ('total_sell_qty', models.CharField(max_length=40)),
                ('lower_circuit', models.CharField(max_length=40)),
                ('upper_circuit', models.CharField(max_length=40)),
                ('yearly_low', models.CharField(max_length=40)),
                ('yearly_high', models.CharField(max_length=40)),
                ('ltt', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.CharField(max_length=40)),
                ('token', models.CharField(max_length=40)),
                ('parent_token', models.CharField(max_length=40)),
                ('symbol', models.CharField(max_length=40)),
                ('name', models.CharField(max_length=40)),
                ('closing_price', models.CharField(max_length=40)),
                ('expiry', models.CharField(max_length=40)),
                ('strike_price', models.FloatField(max_length=40)),
                ('tick_size', models.CharField(max_length=40)),
                ('lot_size', models.CharField(max_length=40)),
                ('instrument_type', models.CharField(max_length=40)),
                ('isin', models.CharField(max_length=40)),
            ],
        ),
    ]
