# Generated by Django 3.2 on 2022-07-21 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the payment method', max_length=50)),
                ('code', models.CharField(help_text='Code to id this method', max_length=10)),
                ('type', models.CharField(choices=[('mobile', 'Mobile Payment'), ('card', 'Card Payment')], default='mobile', help_text='Type of payment method being used', max_length=24)),
                ('islog', models.BooleanField(default=True, help_text='If true payment will be completed later')),
                ('description', models.TextField(default='')),
                ('target', models.CharField(blank=True, max_length=24, null=True)),
                ('is_active', models.BooleanField(default=True, help_text='We can use this to activate or deactivate a payment method')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TransactionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('json_data', models.JSONField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(blank=True, choices=[('702', 'MPESA'), ('700', 'Telkom cash'), ('710', 'Airtell Money'), ('MCK', 'Mastercard Kenya'), ('VCK', 'Visa Kenya')], help_text='Provider of payment services', max_length=50, null=True)),
                ('account_number', models.CharField(max_length=28, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=28, null=True)),
                ('transaction_ref', models.CharField(db_index=True, editable=False, help_text='Unique transaction reference', max_length=40)),
                ('currency', models.CharField(default='KES', max_length=12)),
                ('country', models.CharField(blank=True, max_length=10, null=True)),
                ('city', models.CharField(blank=True, max_length=10, null=True)),
                ('narration', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('Initiated', 'Initiated'), ('Pending', 'Pending'), ('Failed', 'Failed'), ('Successful', 'Successful'), ('Cancelled', 'Cancelled'), ('Reversed', 'Reversed'), ('Failed Completely', 'Failed Completely'), ('Retrying', 'Retrying')], default='Initiated', max_length=50)),
                ('amount', models.PositiveIntegerField()),
                ('error_message', models.TextField(default='')),
                ('instruction_to_customer', models.TextField(default='')),
                ('transaction_is_log', models.BooleanField(default=True, help_text='True means the payment is to be me made later')),
                ('provider_reference', models.CharField(blank=True, max_length=30, null=True)),
                ('amount_paid', models.PositiveIntegerField(default=0)),
                ('last_payment', models.PositiveIntegerField(default=0)),
                ('first_name', models.CharField(blank=True, help_text='first name on card', max_length=40, null=True)),
                ('last_name', models.CharField(blank=True, help_text='last name on card', max_length=40, null=True)),
                ('email', models.EmailField(blank=True, help_text='Card holder email', max_length=70, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=15, null=True)),
                ('street_address', models.CharField(blank=True, max_length=200, null=True)),
                ('initiator_account', models.CharField(blank=True, help_text='sometimes the payment can come from a different account', max_length=70, null=True)),
                ('payment_category', models.CharField(blank=True, choices=[('Checkout', 'Checkout'), ('Topup', 'Topup'), ('Delivery', 'Delivery')], max_length=100, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_edited', models.DateTimeField(auto_now=True, null=True)),
                ('method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='payments.paymentmethod')),
            ],
        ),
    ]
