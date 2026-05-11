# ⚡ Comandos Rápidos - Faturas Automáticas

## 🚀 Iniciar o Sistema

### Iniciar Django + Celery (Desenvolvimento)

```bash
# Terminal 1 - Django
python manage.py runserver

# Terminal 2 - Celery (worker + beat)
celery -A config worker -l info --beat
```

## 🧪 Testar o Sistema

### Executar script de teste completo

```bash
python manage.py shell < test_invoices.py
```

### Executar tasks manualmente

```bash
python manage.py shell
```

```python
# Dentro do shell:

# 1. Criar faturas manualmente
from finances.tasks import create_credit_card_invoices
result = create_credit_card_invoices()
print(result)

# 2. Atualizar faturas atrasadas
from finances.tasks import update_overdue_invoices
result = update_overdue_invoices()
print(result)

# 3. Ver todas as faturas
from finances.models import CreditCardInvoice
for inv in CreditCardInvoice.objects.all():
    print(f"{inv} - R$ {inv.total_amount}")

# 4. Criar transação com cartão (testa signal)
from finances.models import Transaction, CreditCard, Category
from datetime import date

card = CreditCard.objects.first()
cat = Category.objects.filter(type='expense').first()

trans = Transaction.objects.create(
    user=card.user,
    category=cat,
    type='expense',
    description="Teste automático",
    amount=100.00,
    credit_card=card,
    transaction_date=date.today(),
    status='pending'
)

print(f"Transação criada: {trans}")
print(f"Fatura vinculada: {trans.invoice}")

# 5. Ver detalhes de uma fatura
invoice = CreditCardInvoice.objects.first()
print(f"Fatura: {invoice}")
print(f"Total da fatura: R$ {invoice.total_amount}")
print(f"Gastos declarados: R$ {invoice.get_declared_expenses()}")
print(f"Não relacionado: R$ {invoice.get_unrelated_expenses()}")
print(f"Transações: {invoice.transactions.count()}")
print(f"Parcelas: {invoice.installments.count()}")
```

## 🗑️ Limpar Dados de Teste

```bash
python manage.py shell
```

```python
# Deletar transações de teste
from finances.models import Transaction
Transaction.objects.filter(description__icontains='teste').delete()

# Deletar planos de teste
from finances.models import InstallmentPlan
InstallmentPlan.objects.filter(description__icontains='teste').delete()

# Deletar cartão de teste
from finances.models import CreditCard
CreditCard.objects.filter(name='Cartão Teste').delete()

# Deletar faturas de teste (cuidado!)
from finances.models import CreditCardInvoice
# CreditCardInvoice.objects.all().delete()  # Descomente se quiser deletar
```

## 📊 Verificar Status do Sistema

### Ver tasks agendadas do Celery

```bash
python manage.py shell
```

```python
from config.celery import app
schedule = app.conf.beat_schedule

for task_name, config in schedule.items():
    print(f"{task_name}:")
    print(f"  Task: {config['task']}")
    print(f"  Schedule: {config['schedule']}")
    print()
```

### Ver logs do Celery em tempo real

```bash
# Executar com nível de log INFO
celery -A config worker -l info --beat

# Ou com DEBUG para mais detalhes
celery -A config worker -l debug --beat
```

## 🔧 Comandos de Manutenção

### Recalcular totais de faturas

```python
from finances.models import CreditCardInvoice

for invoice in CreditCardInvoice.objects.all():
    declared = invoice.get_declared_expenses()
    invoice.total_amount = declared
    invoice.save()
    print(f"{invoice} → R$ {declared}")
```

### Vincular transações órfãs às faturas

```python
from finances.models import Transaction
from finances.services import InvoiceService

service = InvoiceService()

# Buscar transações com cartão mas sem fatura
orphan_transactions = Transaction.objects.filter(
    credit_card__isnull=False,
    invoice__isnull=True
)

for trans in orphan_transactions:
    invoice = service.link_transaction_to_invoice(trans)
    print(f"{trans.description} → {invoice}")
```

### Verificar integridade

```python
from finances.models import CreditCard, CreditCardInvoice

# Verificar duplicatas (não deveria ter!)
from django.db.models import Count

duplicates = CreditCardInvoice.objects.values(
    'credit_card', 'reference_month'
).annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicates.exists():
    print("⚠️ Duplicatas encontradas!")
    for dup in duplicates:
        print(dup)
else:
    print("✅ Nenhuma duplicata (correto!)")
```

## 📈 Relatórios Rápidos

### Resumo por cartão

```python
from finances.models import CreditCard, CreditCardInvoice
from django.db.models import Sum, Count

for card in CreditCard.objects.filter(is_active=True):
    invoices = card.invoices.all()
    
    print(f"\n{card.name}")
    print(f"  Faturas: {invoices.count()}")
    print(f"  Total faturado: R$ {invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0}")
    print(f"  Pendentes: {invoices.filter(status='pending').count()}")
    print(f"  Atrasadas: {invoices.filter(status='overdue').count()}")
    print(f"  Pagas: {invoices.filter(status='paid').count()}")
```

### Faturas do mês atual

```python
from finances.models import CreditCardInvoice
from datetime import date

current_month = date(date.today().year, date.today().month, 1)

invoices = CreditCardInvoice.objects.filter(
    reference_month=current_month
)

print(f"Faturas de {current_month.strftime('%m/%Y')}:\n")
for inv in invoices:
    print(f"{inv.credit_card.name}:")
    print(f"  Total: R$ {inv.total_amount}")
    print(f"  Vencimento: {inv.due_date}")
    print(f"  Status: {inv.get_status_display()}")
    print()
```

## 🐛 Debug

### Verificar se signals estão funcionando

```python
from django.db.models import signals
from finances.models import Transaction
from finances import signals as finance_signals

# Ver receivers registrados
print("Receivers para Transaction.post_save:")
for receiver in signals.post_save.receivers:
    print(receiver)
```

### Testar manualmente o serviço

```python
from finances.services import InvoiceService
from finances.models import CreditCard
from datetime import date

service = InvoiceService()
card = CreditCard.objects.first()

# Testar cálculo de datas
reference_month = date(2025, 10, 1)
closing, due = service.calculate_invoice_dates(card, reference_month)
print(f"Fechamento: {closing}")
print(f"Vencimento: {due}")

# Testar criação de fatura
invoice, created = service.get_or_create_invoice(card, reference_month)
print(f"Fatura: {invoice}")
print(f"Criada: {created}")
```

## 🎯 Dicas

### Forçar execução imediata de uma task periódica

```bash
python manage.py shell
```

```python
from finances.tasks import create_credit_card_invoices
create_credit_card_invoices.apply()  # Executa imediatamente
```

### Ver próximas execuções do Celery Beat

```bash
celery -A config inspect scheduled
```

### Monitorar Celery com Flower (opcional)

```bash
pip install flower
celery -A config flower
# Acesse http://localhost:5555
```

