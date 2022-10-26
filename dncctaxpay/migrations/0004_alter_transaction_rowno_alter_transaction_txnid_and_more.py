# Generated by Django 4.0.4 on 2022-10-25 06:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dncctaxpay', '0003_transaction_branch_user_branchname_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='rowNo',
            field=models.CharField(editable=False, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='txnId',
            field=models.CharField(editable=False, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='txn_date',
            field=models.DateTimeField(default=datetime.datetime(2022, 10, 25, 12, 11, 30, 852429), editable=False, null=True),
        ),
    ]