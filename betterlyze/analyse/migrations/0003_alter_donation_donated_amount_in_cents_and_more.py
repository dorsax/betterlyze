# Generated by Django 4.2.6 on 2023-10-22 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyse', '0002_auto_20221110_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='donated_amount_in_cents',
            field=models.BigIntegerField(verbose_name='Spende in Cents'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='donated_at',
            field=models.DateTimeField(verbose_name='Spendenzeitpunkt'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='donor',
            field=models.CharField(default='Anonym', max_length=255, verbose_name='Spender'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='message',
            field=models.TextField(default='', verbose_name='Nachricht'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='page',
            field=models.BigIntegerField(verbose_name='Seite'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='was_zero',
            field=models.IntegerField(default=0, verbose_name='Geldbetrag anonym'),
        ),
    ]
