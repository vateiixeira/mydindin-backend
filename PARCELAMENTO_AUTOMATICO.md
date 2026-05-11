# 📦 Sistema de Parcelamento com Transações Automáticas

## 🎯 Funcionalidade Implementada

Quando você cria um `InstallmentPlan` (plano de parcelamento), o sistema agora cria **automaticamente**:

1. ✅ **Todas as parcelas** (`Installment`)
2. ✅ **Uma transação (`Transaction`) para cada parcela**
3. ✅ **Vincula cada parcela à sua transação**
4. ✅ **Se tiver cartão de crédito, vincula à fatura correta**

## 🚀 Como Funciona

### Criando um Parcelamento

```python
from finances.models import InstallmentPlan, CreditCard, Category
from datetime import date
from decimal import Decimal

# Buscar cartão e categoria
card = CreditCard.objects.get(name="Nubank")
category = Category.objects.get(name="Eletrônicos", type="expense")

# Criar parcelamento
plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Notebook Dell 12x",
    credit_card=card,           # ← Vincula ao cartão
    total_installments=12,      # 12 parcelas
    default_amount=Decimal('500.00'),  # R$ 500 cada
    start_date=date(2025, 11, 5),  # Primeira parcela em 05/11
    is_active=True
)
```

### O Que Acontece Automaticamente

```
┌──────────────────────────────────────────────────┐
│ 1. InstallmentPlan é criado                      │
└────────────────┬─────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────┐
│ 2. Método _create_installments() é chamado      │
└────────────────┬─────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────┐
│ 3. Cria 12 parcelas (Installment)               │
│    - Parcela 1: 05/11/2025 - R$ 500             │
│    - Parcela 2: 05/12/2025 - R$ 500             │
│    - Parcela 3: 05/01/2026 - R$ 500             │
│    - ... (e assim por diante)                    │
└────────────────┬─────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────┐
│ 4. Cria 12 transações (Transaction)             │
│    - "Notebook Dell 12x - Parcela 1/12"         │
│    - "Notebook Dell 12x - Parcela 2/12"         │
│    - ... (uma para cada parcela)                 │
└────────────────┬─────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────┐
│ 5. Vincula cada Transaction à sua Installment   │
│    installment.transaction = transaction_obj     │
│    installment.status = 'generated'              │
└────────────────┬─────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────┐
│ 6. Signal auto_link_transaction_to_invoice       │
│    vincula cada transação à fatura correta       │
│    (se houver cartão de crédito)                 │
└──────────────────────────────────────────────────┘
```

## 📊 Exemplo Completo

### Criar Parcelamento com Cartão

```python
from finances.models import InstallmentPlan
from datetime import date

# Criar parcelamento de 6x
plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="iPhone 15 Pro 6x",
    credit_card=card,
    total_installments=6,
    default_amount=Decimal('1000.00'),
    start_date=date(2025, 11, 5),
    is_active=True
)

# Verificar o que foi criado
print(f"Plano criado: {plan.description}")
print(f"Total de parcelas: {plan.installments.count()}")  # 6

# Ver as parcelas
for inst in plan.installments.all():
    print(f"\nParcela {inst.installment_number}:")
    print(f"  Vencimento: {inst.due_date}")
    print(f"  Valor: R$ {inst.amount}")
    print(f"  Status: {inst.get_status_display()}")  # 'Transação Gerada'
    print(f"  Transação: {inst.transaction.id}")
    print(f"  Fatura: {inst.transaction.invoice}")

# Output esperado:
# Parcela 1:
#   Vencimento: 2025-11-05
#   Valor: R$ 1000.00
#   Status: Transação Gerada
#   Transação: 123
#   Fatura: Nubank - 11/2025
#
# Parcela 2:
#   Vencimento: 2025-12-05
#   Valor: R$ 1000.00
#   Status: Transação Gerada
#   Transação: 124
#   Fatura: Nubank - 12/2025
# ...
```

### Criar Parcelamento SEM Cartão

```python
# Parcelamento sem cartão (boleto, débito, etc)
plan_no_card = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Consórcio Imóvel 120x",
    credit_card=None,  # ← SEM cartão
    total_installments=120,
    default_amount=Decimal('1500.00'),
    start_date=date(2025, 11, 15),
    is_active=True
)

# Ainda assim cria transações, mas SEM fatura
print(f"Parcelas criadas: {plan_no_card.installments.count()}")  # 120
print(f"Transações criadas: {plan_no_card.installments.first().transaction}")  # Existe
print(f"Tem fatura? {plan_no_card.installments.first().transaction.invoice}")  # None
```

## 🔧 Detalhes Técnicos

### Status das Parcelas

Após a criação, as parcelas têm:
- **Status:** `'generated'` (Transação Gerada)
- **Transaction:** Vinculada
- **Invoice:** Vinculada (se tiver cartão)

### Campos da Transaction Criada

```python
transaction = Transaction(
    user=plan.user,
    category=plan.category,
    type=plan.type,
    description=f"{plan.description} - Parcela {n}/{total}",
    amount=installment.amount,
    credit_card=plan.credit_card,  # Pode ser None
    transaction_date=installment.due_date,  # Data = vencimento
    due_date=installment.due_date,
    status='pending',
    notes=f"Gerado automaticamente do parcelamento {plan.description}"
)
```

### Otimização com Bulk Operations

O método usa operações em massa para performance:

```python
# Cria todas as parcelas de uma vez
Installment.objects.bulk_create(installments_to_create)

# Cria todas as transações de uma vez
Transaction.objects.bulk_create(transactions_to_create)

# Atualiza todas as parcelas de uma vez
Installment.objects.bulk_update(created_installments, ['transaction', 'status'])
```

## 🧪 Como Testar

### Script de Teste Completo

```bash
python manage.py shell < test_installment_transactions.py
```

### Teste Manual

```python
from finances.models import InstallmentPlan, Transaction, Installment
from datetime import date

# Criar parcelamento
plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Teste 3x",
    credit_card=card,
    total_installments=3,
    default_amount=Decimal('100.00'),
    start_date=date.today(),
    is_active=True
)

# Verificar
assert plan.installments.count() == 3, "Deveria ter 3 parcelas"

for inst in plan.installments.all():
    assert inst.transaction is not None, f"Parcela {inst.installment_number} deve ter transação"
    assert inst.status == 'generated', f"Parcela {inst.installment_number} deve ter status 'generated'"
    assert inst.transaction.credit_card == card, "Transação deve ter cartão vinculado"
    assert inst.transaction.invoice is not None, "Transação deve ter fatura vinculada"

print("✅ Todos os testes passaram!")
```

## 📋 Vantagens

### Antes (Sistema Antigo)

```python
# Criar parcelamento
plan = InstallmentPlan.objects.create(...)

# Parcelas criadas, mas SEM transações
# Transações só eram criadas depois, pelo Celery
# Dias/semanas depois quando o vencimento se aproximava
```

**Problemas:**
- ❌ Transações não aparecem no histórico imediatamente
- ❌ Usuário não vê o impacto futuro das parcelas
- ❌ Difícil de planejar fluxo de caixa

### Agora (Sistema Novo)

```python
# Criar parcelamento
plan = InstallmentPlan.objects.create(...)

# TUDO criado imediatamente:
# ✅ 12 parcelas
# ✅ 12 transações
# ✅ Vinculadas às faturas corretas
```

**Benefícios:**
- ✅ Histórico completo imediatamente
- ✅ Usuário vê todas as parcelas futuras
- ✅ Planejamento de fluxo de caixa facilitado
- ✅ Faturas já mostram parcelas futuras

## 🎓 Casos de Uso

### 1. Compra Parcelada no Cartão

```python
InstallmentPlan.objects.create(
    description="Smart TV 10x",
    credit_card=card,
    total_installments=10,
    default_amount=Decimal('300.00'),
    start_date=date(2025, 11, 5)
)
# ✅ 10 transações criadas
# ✅ Cada uma vinculada à fatura do mês correto
# ✅ Usuário vê impacto nas próximas 10 faturas
```

### 2. Financiamento / Consórcio (SEM Cartão)

```python
InstallmentPlan.objects.create(
    description="Financiamento Carro 48x",
    credit_card=None,  # Boleto bancário
    total_installments=48,
    default_amount=Decimal('800.00'),
    start_date=date(2025, 11, 10)
)
# ✅ 48 transações criadas
# ✅ SEM vínculo com faturas de cartão
# ✅ Aparecem no histórico/planejamento
```

### 3. Recebimento Parcelado (Receita)

```python
InstallmentPlan.objects.create(
    type='income',  # Receita!
    description="Venda de produto 6x",
    credit_card=None,
    total_installments=6,
    default_amount=Decimal('500.00'),
    start_date=date(2025, 11, 15)
)
# ✅ 6 transações de RECEITA criadas
# ✅ Planejamento de recebimentos futuros
```

## 🔍 Consultas Úteis

### Ver todas as transações de um parcelamento

```python
plan = InstallmentPlan.objects.get(id=1)

# Opção 1: Via parcelas
for inst in plan.installments.all():
    print(inst.transaction)

# Opção 2: Via query
Transaction.objects.filter(
    notes__icontains=f"parcelamento {plan.description}"
)
```

### Verificar integridade

```python
# Verificar se todas as parcelas têm transação
plan = InstallmentPlan.objects.get(id=1)

parcelas_sem_transacao = plan.installments.filter(
    transaction__isnull=True
).count()

if parcelas_sem_transacao > 0:
    print(f"⚠️ {parcelas_sem_transacao} parcelas sem transação!")
else:
    print("✅ Todas as parcelas têm transação")
```

## 🐛 Troubleshooting

### Parcelas foram criadas mas transações não

**Possível causa:** Erro durante a criação

**Solução:** Usar transações atômicas (já implementado)
```python
with db_transaction.atomic():
    # Se algo falhar, TUDO é revertido
    # Não ficam parcelas órfãs
```

### Transações duplicadas

**Não deve acontecer!** Cada parcela tem apenas 1 transação vinculada via `OneToOneField`.

### Performance com muitas parcelas

**Otimizado!** Usa `bulk_create` e `bulk_update`:
- 120 parcelas = 3 queries (não 240!)
- 120 transações = 1 query (não 120!)

## 📚 Resumo

**Ao criar um `InstallmentPlan`:**

| Ação | Resultado |
|------|-----------|
| `plan.save()` | Chama `_create_installments()` |
| `_create_installments()` | Cria N parcelas + N transações |
| Cada `Installment` | Tem `transaction` vinculada |
| Cada `Transaction` | Criada com todos os campos corretos |
| Se tem `credit_card` | Signal vincula à fatura automaticamente |
| Status da parcela | `'generated'` (Transação Gerada) |

**Tudo automático, tudo registrado, desde o início! 🚀**

