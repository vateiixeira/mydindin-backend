import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0004_add_payment_method_and_recurring_card'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditcardinvoice',
            name='payment_transaction',
            field=models.OneToOneField(
                blank=True,
                help_text='Transação bancária que representa o pagamento desta fatura',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoice_payment',
                to='finances.transaction',
                verbose_name='Transação de Pagamento',
            ),
        ),
    ]
