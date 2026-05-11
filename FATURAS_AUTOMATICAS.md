# Sistema de Faturas Automáticas de Cartão de Crédito

## 📋 Visão Geral

Sistema automatizado para gerenciamento de faturas de cartão de crédito com jobs do Celery.

## 🎯 Funcionalidades Implementadas

### 1. Criação Automática de Faturas (Task Periódica)

**Task:** `finances.create_credit_card_invoices`
- **Execução:** Diariamente às 00:15
- **Função:** Cria faturas automaticamente quando a data de fechamento (`closing_date`) está no passado
- **Garantia:** Apenas 1 fatura por `reference_month` (unique_together no modelo)

**Como funciona:**
1. Busca todos os cartões ativos (`is_active=True`)
2. Para cada cartão, verifica se a data de fechamento do mês atual já passou
3. Se sim, cria uma fatura para o mês de referência (se não existir)
4. Também cria a fatura do próximo mês após o fechamento do mês atual

**Exemplo:**
- Cartão com `closing_day=15` e `due_day=20`
- Data atual: 16/10/2025
- Como o dia 15 já passou, cria:
  - Fatura de outubro (reference_month: 01/10/2025, closing: 15/10, vencimento: 20/11)
  - Fatura de novembro (reference_month: 01/11/2025, closing: 15/11, vencimento: 20/12)

### 2. Vinculação Automática de Transações (Signals)

**Signal:** `auto_link_transaction_to_invoice`
- **Trigger:** Quando uma `Transaction` é criada ou atualizada
- **Condição:** Transaction tem `credit_card` mas não tem `invoice`
- **Ação:** Vincula automaticamente à fatura correta ou cria se não existir

**Como funciona:**
1. Detecta quando uma transação tem cartão de crédito
2. Calcula qual mês de referência da fatura baseado na `transaction_date` e `closing_day`
3. Busca ou cria a fatura para aquele mês
4. Vincula a transação à fatura
5. Atualiza o `total_amount` da fatura

**Regra de vencimento:**
- Transação antes do dia de fechamento → fatura do mês atual
- Transação após o dia de fechamento → fatura do próximo mês

**Exemplo:**
- Cartão com `closing_day=15`
- Transação em 10/10/2025 → vai para fatura de outubro
- Transação em 20/10/2025 → vai para fatura de novembro

### 3. Vinculação Automática de Parcelas (Signals)

**Signal:** `auto_link_installment_to_invoice`
- **Trigger:** Quando uma `Installment` é criada ou atualizada
- **Condição:** Parcela tem `plan.credit_card` mas não tem `invoice`
- **Ação:** Vincula automaticamente à fatura correta

**Como funciona:**
1. Detecta quando uma parcela pertence a um plano com cartão de crédito
2. Usa a `due_date` da parcela para calcular o mês de referência
3. Busca ou cria a fatura correspondente
4. Vincula a parcela à fatura
5. Atualiza o `total_amount` da fatura

### 4. Atualização de Status (Task Periódica)

**Task:** `finances.update_overdue_invoices`
- **Execução:** Diariamente às 00:20
- **Função:** Marca faturas como atrasadas quando `due_date < hoje` e `status='pending'`

## 🔧 Arquivos Criados/Modificados

### Novos Arquivos

1. **`finances/services/invoice_service.py`**
   - `InvoiceService`: Serviço com toda lógica de faturas
   - Métodos principais:
     - `get_invoice_month_for_transaction()`: Calcula mês de referência
     - `calculate_invoice_dates()`: Calcula datas de fechamento/vencimento
     - `get_or_create_invoice()`: Obtém ou cria fatura (garante unicidade)
     - `create_pending_invoices()`: Cria faturas pendentes (task periódica)
     - `link_transaction_to_invoice()`: Vincula transação à fatura
     - `link_installment_to_invoice()`: Vincula parcela à fatura
     - `update_invoice_total()`: Atualiza total da fatura
     - `update_overdue_invoices()`: Marca faturas atrasadas

2. **`finances/signals.py`**
   - `auto_link_transaction_to_invoice`: Signal para Transaction
   - `auto_link_installment_to_invoice`: Signal para Installment

### Arquivos Modificados

1. **`finances/tasks.py`**
   - Adicionadas 3 novas tasks:
     - `create_credit_card_invoices()`: Task periódica
     - `update_overdue_invoices()`: Task periódica
     - `link_transaction_to_invoice_task()`: Task assíncrona (opcional)

2. **`finances/apps.py`**
   - Adicionado método `ready()` para registrar signals

3. **`finances/services/__init__.py`**
   - Exportado `InvoiceService`

4. **`config/celery.py`**
   - Adicionadas 2 novas tasks ao beat_schedule:
     - `create-credit-card-invoices`: 00:15 diariamente
     - `update-overdue-invoices`: 00:20 diariamente

## 🧪 Como Testar

### 1. Teste Manual - Criar Transação com Cartão

```python
from finances.models import CreditCard, Transaction, Category
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()
user = User.objects.first()

# Criar um cartão
card = CreditCard.objects.create(
    user=user,
    name="Nubank Platinum",
    brand="visa",
    closing_day=15,  # Fecha dia 15
    due_day=25,      # Vence dia 25
    credit_limit=5000,
    is_active=True
)

# Criar uma categoria de despesa
category = Category.objects.filter(type='expense', user=user).first()

# Criar transação ANTES do fechamento (vai para fatura do mês atual)
transaction1 = Transaction.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Compra no supermercado",
    amount=150.00,
    credit_card=card,  # Aqui vincula ao cartão
    transaction_date=date(2025, 10, 10),  # Antes do dia 15
    status='pending'
)
# ✅ Signal vai criar/vincular à fatura de outubro automaticamente

# Criar transação DEPOIS do fechamento (vai para fatura do próximo mês)
transaction2 = Transaction.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Compra na farmácia",
    amount=80.00,
    credit_card=card,
    transaction_date=date(2025, 10, 20),  # Depois do dia 15
    status='pending'
)
# ✅ Signal vai criar/vincular à fatura de novembro automaticamente

# Verificar faturas criadas
from finances.models import CreditCardInvoice
invoices = CreditCardInvoice.objects.filter(credit_card=card)
for invoice in invoices:
    print(f"Fatura: {invoice.reference_month.strftime('%m/%Y')}")
    print(f"  Fechamento: {invoice.closing_date}")
    print(f"  Vencimento: {invoice.due_date}")
    print(f"  Total declarado: R$ {invoice.get_declared_expenses()}")
    print(f"  Transações: {invoice.transactions.count()}")
    print()
```

### 2. Teste da Task Periódica

```python
from finances.tasks import create_credit_card_invoices

# Executar task manualmente
result = create_credit_card_invoices()
print(result)
# Exemplo de output:
# {
#   'processed': 2,
#   'created': 3,
#   'skipped': 1,
#   'errors': []
# }
```

### 3. Teste com Parcelamento

```python
from finances.models import InstallmentPlan
from datetime import date

# Criar plano parcelado no cartão
plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Notebook Parcelado",
    credit_card=card,  # Vincula ao cartão
    total_installments=12,
    default_amount=200.00,
    start_date=date(2025, 10, 5),  # Primeira parcela em 05/10
    is_active=True
)

# Verificar parcelas criadas
parcelas = plan.installments.all()
for parcela in parcelas[:3]:
    print(f"Parcela {parcela.installment_number}: {parcela.due_date} - Fatura: {parcela.invoice}")
# ✅ Cada parcela já foi vinculada à fatura correta pelo signal
```

### 4. Teste de Atualização de Status

```python
from finances.tasks import update_overdue_invoices
from datetime import date, timedelta

# Criar fatura com vencimento no passado
past_invoice = CreditCardInvoice.objects.create(
    credit_card=card,
    reference_month=date(2025, 9, 1),
    total_amount=500.00,
    closing_date=date(2025, 9, 15),
    due_date=date(2025, 9, 25) - timedelta(days=30),  # Vencida
    status='pending'
)

# Executar task
result = update_overdue_invoices()
print(f"Faturas atualizadas: {result['invoices_updated']}")

# Verificar status
past_invoice.refresh_from_db()
print(f"Status: {past_invoice.status}")  # Deve ser 'overdue'
```

## 📊 Fluxo Completo

```
1. Usuário cria Transaction com credit_card
   ↓
2. Signal auto_link_transaction_to_invoice é disparado
   ↓
3. InvoiceService calcula mês de referência
   ↓
4. InvoiceService busca fatura ou cria se não existir
   ↓
5. Transaction é vinculada à fatura
   ↓
6. total_amount da fatura é atualizado
   ↓
7. Todo dia às 00:15, task create_credit_card_invoices roda
   ↓
8. Cria faturas para meses onde closing_date já passou
   ↓
9. Todo dia às 00:20, task update_overdue_invoices roda
   ↓
10. Marca faturas vencidas como 'overdue'
```

## 🚀 Executar o Celery

### Iniciar Worker

```bash
celery -A config worker -l info
```

### Iniciar Beat (tarefas periódicas)

```bash
celery -A config beat -l info
```

### Executar ambos simultaneamente (desenvolvimento)

```bash
celery -A config worker -l info --beat
```

## 📌 Observações Importantes

1. **Unicidade garantida**: O modelo tem `unique_together = [['credit_card', 'reference_month']]`, então nunca haverá faturas duplicadas.

2. **Signals vs Tasks**: 
   - Signals processam em tempo real quando Transaction/Installment é criada
   - Tasks periódicas garantem que faturas sejam criadas mesmo sem transações

3. **Cálculo inteligente de mês**: 
   - Considera o `closing_day` do cartão
   - Transações após o fechamento vão para o próximo mês

4. **Atualização automática de totais**:
   - `get_declared_expenses()` soma Transactions + Installments
   - `total_amount` pode ser maior (gastos não declarados)

5. **Performance**:
   - Signals são síncronos (podem bloquear se houver muitas transações)
   - Para importação em massa, considere desabilitar signals temporariamente

## 🔍 Monitoramento

Ver logs do Celery para acompanhar execução:

```
[CreditCardInvoices] Processados: 5, Criados: 3, Ignorados: 2, Erros: 0
  ✓ Fatura criada: Nubank Platinum - 10/2025
  ✓ Fatura criada: Itaú Gold - 10/2025
  
[UpdateOverdueInvoices] Faturas atualizadas: 2
```

## 🐛 Troubleshooting

### Fatura não foi criada automaticamente

1. Verificar se o cartão está ativo: `credit_card.is_active == True`
2. Verificar se a data de fechamento já passou
3. Verificar logs do Celery Beat
4. Executar task manualmente para debug

### Transação não foi vinculada à fatura

1. Verificar se a transação tem `credit_card` definido
2. Verificar se signals estão registrados (apps.py)
3. Verificar logs de erros no console

### Total da fatura não atualiza

1. Método `update_invoice_total()` só aumenta o total, nunca diminui
2. Para recalcular: `invoice.total_amount = invoice.get_declared_expenses(); invoice.save()`

