# Generated by Django 4.2.4 on 2023-09-29 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_control_system', '0008_rename_invoice_number_salemaster_invoice_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasemaster',
            name='invoice_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='salemaster',
            name='invoice_date',
            field=models.DateField(),
        ),
    ]
