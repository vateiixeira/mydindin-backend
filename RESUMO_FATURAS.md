# 🎯 Sistema de Faturas Automáticas - Resumo

## ✅ O que foi implementado

### 1. **Criação Automática de Faturas (Job Celery)**

**Task periódica:** `create_credit_card_invoices`
- Roda **diariamente às 00:15**
- Cria faturas quando `closing_date` está no passado
- Garante que **só existe 1 fatura por mês** (unique_together)
- Processa todos os cartões ativos

### 2. **Vinculação Automática ao Criar Transação**

**Signal:** `auto_link_transaction_to_invoice`
- Dispara **automaticamente** quando você cria uma `Transaction` com `credit_card`
- Calcula automaticamente qual fatura a transação pertence
- **Cria a fatura se não existir**
- Atualiza o total da fatura

**Lógica:**
- Transação **antes** do dia de fechamento → vai para fatura do mês atual
- Transação **depois** do dia de fechamento → vai para fatura do próximo mês

### 3. **Vinculação Automática de Parcelas**

**Signal:** `auto_link_installment_to_invoice`
- Dispara quando você cria um `InstallmentPlan` com `credit_card`
- Cada parcela é vinculada automaticamente à fatura correta
- Também cria a fatura se não existir

### 4. **Atualização de Status**

**Task periódica:** `update_overdue_invoices`
- Roda **diariamente às 00:20**
- Marca faturas como "Atrasado" quando vencimento passou

## 📁 Arquivos Criados

```
finances/
├── services/
│   └── invoice_service.py          ← Serviço com toda lógica de faturas
├── signals.py                       ← Signals para automação
├── tasks.py                         ← Tasks do Celery (atualizadas)
└── apps.py                          ← Registra os signals

config/
└── celery.py                        ← Configuração do Celery Beat (atualizada)

FATURAS_AUTOMATICAS.md              ← Documentação completa
RESUMO_FATURAS.md                   ← Este arquivo
test_invoices.py                    ← Script de teste
```

## 🚀 Como Usar

### Uso Normal (Automático)

Simplesmente crie transações com cartão de crédito:

```python
from finances.models import Transaction, CreditCard

card = CreditCard.objects.get(name="Nubank")

# Criar transação - a fatura é criada/vinculada automaticamente!
Transaction.objects.create(
    user=user,
    category=categoria,
    type='expense',
    description="Compra no supermercado",
    amount=150.00,
    credit_card=card,           # ← Só precisa informar o cartão
    transaction_date=date.today(),
    status='pending'
)
# ✅ Signal cria/vincula à fatura automaticamente
```

### Parcelamento com Cartão

```python
from finances.models import InstallmentPlan

# Criar parcelamento - parcelas são vinculadas automaticamente!
InstallmentPlan.objects.create(
    user=user,
    category=categoria,
    type='expense',
    description="Notebook 12x",
    credit_card=card,           # ← Vincular ao cartão
    total_installments=12,
    default_amount=200.00,
    start_date=date.today(),
    is_active=True
)
# ✅ Todas as 12 parcelas são vinculadas às faturas corretas
```

## ⏰ Tasks Automáticas do Celery

Configuradas para rodar automaticamente:

| Horário | Task | Função |
|---------|------|--------|
| 00:01 | `create_recurring_transactions` | Cria transações recorrentes |
| 00:05 | `create_installment_transactions` | Cria transações de parcelas |
| 00:10 | `update_overdue_status` | Atualiza transações atrasadas |
| **00:15** | **`create_credit_card_invoices`** | **Cria faturas de cartão** |
| **00:20** | **`update_overdue_invoices`** | **Atualiza faturas atrasadas** |

## 🧪 Como Testar

### Opção 1: Usar o script de teste

```bash
python manage.py shell < test_invoices.py
```

Ou dentro do shell:

```bash
python manage.py shell
>>> exec(open('test_invoices.py').read())
```

### Opção 2: Executar task manualmente

```python
from finances.tasks import create_credit_card_invoices

# Executar manualmente
result = create_credit_card_invoices()
print(result)
```

### Opção 3: Teste rápido no admin

1. Acesse o admin Django
2. Crie um cartão de crédito
3. Crie uma transação vinculada ao cartão
4. **Verifique que a fatura foi criada automaticamente!**

## 🔍 Como Verificar se Está Funcionando

### Ver faturas criadas

```python
from finances.models import CreditCardInvoice

# Ver todas as faturas
for invoice in CreditCardInvoice.objects.all():
    print(f"Fatura: {invoice}")
    print(f"  Total declarado: R$ {invoice.get_declared_expenses()}")
    print(f"  Transações: {invoice.transactions.count()}")
    print(f"  Parcelas: {invoice.installments.count()}")
```

### Ver logs do Celery

Quando as tasks rodarem, você verá logs como:

```
[CreditCardInvoices] Processados: 3, Criados: 2, Ignorados: 1, Erros: 0
  ✓ Fatura criada: Nubank Platinum - 10/2025
  ✓ Fatura criada automaticamente para parcela: Nubank - 11/2025
```

## ⚙️ Executar o Celery

### Desenvolvimento (worker + beat juntos)

```bash
celery -A config worker -l info --beat
```

### Produção (separado)

Terminal 1 - Worker:
```bash
celery -A config worker -l info
```

Terminal 2 - Beat:
```bash
celery -A config beat -l info
```

## 📊 Exemplo de Fluxo Completo

```
1. Usuário tem cartão com closing_day=15
   ↓
2. Usuário cria transação no dia 10/10
   ↓
3. Signal detecta credit_card na transação
   ↓
4. InvoiceService calcula: dia 10 < dia 15 → fatura de outubro
   ↓
5. Busca fatura de outubro
   ↓
6. Se não existe, cria automaticamente:
   - reference_month: 01/10/2025
   - closing_date: 15/10/2025
   - due_date: 15/11/2025
   ↓
7. Vincula transação à fatura
   ↓
8. Atualiza total_amount da fatura
   ↓
9. Todo dia 00:15, task verifica se precisa criar mais faturas
   ↓
10. Todo dia 00:20, task marca faturas vencidas como atrasadas
```

## 🎓 Regras de Negócio

### Cálculo do Mês de Referência

Para **transações**:
```python
if transaction_date.day <= closing_day:
    # Fatura do mês atual
    reference_month = primeiro_dia_do_mes_atual
else:
    # Fatura do próximo mês
    reference_month = primeiro_dia_do_proximo_mes
```

### Unicidade de Faturas

```python
unique_together = [['credit_card', 'reference_month']]
```

Garante que **nunca** existirão 2 faturas do mesmo mês para o mesmo cartão.

### Atualização de Total

```python
total_declarado = transações + parcelas
if total_declarado > total_atual:
    total_atual = total_declarado
```

O total só **aumenta**, nunca diminui (preserva valores manuais).

## ❓ Troubleshooting

### Fatura não foi criada

✅ Verifique:
- Cartão está ativo (`is_active=True`)
- Transaction tem `credit_card` definido
- Signals estão registrados (apps.py)

### Transação não foi vinculada

✅ Verifique:
- Signal `auto_link_transaction_to_invoice` está ativo
- Não há erros nos logs
- `credit_card` foi definido na transação

### Total da fatura está errado

```python
# Recalcular manualmente
invoice.total_amount = invoice.get_declared_expenses()
invoice.save()
```

## 📚 Documentação Adicional

- **FATURAS_AUTOMATICAS.md** → Documentação completa e detalhada
- **test_invoices.py** → Script de teste completo
- **CARTOES_CREDITO_API.md** → Documentação da API REST

## 🎉 Pronto para Usar!

O sistema está **100% funcional** e **totalmente automático**:

✅ Faturas são criadas automaticamente  
✅ Transações são vinculadas automaticamente  
✅ Parcelas são vinculadas automaticamente  
✅ Status são atualizados automaticamente  
✅ Jobs do Celery rodam diariamente  

**Você só precisa:**
1. Criar cartões de crédito
2. Criar transações vinculadas aos cartões
3. O resto é automático! 🚀

