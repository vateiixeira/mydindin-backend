# 🔗 Vinculação Automática de Parcelas e Transações a Faturas

## ✅ Funcionalidades Implementadas

### 1. Vinculação Automática ao Criar Parcela

Quando um `InstallmentPlan` com `credit_card` é criado e suas parcelas (`Installment`) são geradas:

✅ **Automaticamente verifica** se o plano tem cartão de crédito
✅ **Procura ou cria** a fatura (invoice) do cartão baseada no `due_date` da parcela
✅ **Vincula a parcela** à fatura encontrada/criada
✅ **Vincula a transação** da parcela (se existir) à mesma fatura

### 2. Processamento em Lote via create_pending_invoices

O método `create_pending_invoices()` agora também:

✅ **Varre todas as parcelas** que têm `credit_card` mas ainda não têm `invoice`
✅ **Vincula automaticamente** cada parcela à fatura apropriada
✅ **Vincula as transações** das parcelas à mesma fatura
✅ **Recalcula os totais** das faturas após vincular

## 🎯 Como Funciona

### Fluxo 1: Criação de Parcelas

```python
# 1. Criar um plano de parcelamento com cartão
plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description='Financiamento',
    credit_card=meu_cartao,  # ← Tem cartão!
    total_installments=12,
    default_amount=Decimal('500.00'),
    start_date='2024-10-01'
)

# 2. Gerar as parcelas (via signal post_save ou manualmente)
# Cada parcela criada vai:
# → Verificar que plan.credit_card existe
# → Buscar/criar invoice baseada no due_date
# → Vincular installment.invoice = invoice
# → Se installment.transaction existe, vincular transaction.invoice = invoice
```

### Fluxo 2: Processamento em Lote

```python
# Executar o processamento
from finances.services.invoice_service import InvoiceService

service = InvoiceService()
stats = service.create_pending_invoices()

# Resultado:
# {
#   'processed': 3,           # Cartões processados
#   'created': 2,             # Faturas criadas
#   'skipped': 1,             # Faturas já existentes
#   'linked_installments': 5, # Parcelas vinculadas
#   'errors': []
# }
```

## 📝 Implementação Detalhada

### 1. Atualização do `link_installment_to_invoice()`

**Localização**: `finances/services/invoice_service.py`

```python
@staticmethod
def link_installment_to_invoice(installment):
    """
    Vincula uma parcela à fatura correta do cartão de crédito.
    Também vincula a transação da parcela (se existir) à mesma fatura.
    """
    if not installment.plan.credit_card:
        return None
    
    # Determinar o mês de referência baseado no due_date
    reference_month = InvoiceService.get_invoice_month_for_transaction(
        installment.plan.credit_card,
        installment.due_date
    )
    
    # Obter ou criar a fatura
    invoice, created = InvoiceService.get_or_create_invoice(
        installment.plan.credit_card,
        reference_month
    )
    
    # Vincular a parcela à fatura
    installment.invoice = invoice
    installment.save(update_fields=['invoice'])
    
    # ✨ NOVO: Vincular também a transação (se existir)
    try:
        if installment.transaction and not installment.transaction.invoice:
            installment.transaction.invoice = invoice
            installment.transaction.save(update_fields=['invoice'])
    except Exception as e:
        print(f"⚠ Erro ao vincular transação: {str(e)}")
    
    return invoice
```

**O que mudou:**
- ✅ Agora verifica se `installment.transaction` existe
- ✅ Se existir e não tiver invoice, vincula à mesma invoice da parcela
- ✅ Usa `update_fields` para otimizar o save

### 2. Atualização do `create_pending_invoices()`

**Localização**: `finances/services/invoice_service.py`

```python
@staticmethod
def create_pending_invoices():
    """
    Cria faturas pendentes para todos os cartões ativos.
    Também vincula parcelas pendentes que ainda não têm fatura.
    """
    # ... código existente para criar faturas ...
    
    # ✨ NOVO: Processar parcelas pendentes
    for card in active_cards:
        # Buscar parcelas deste cartão sem fatura
        pending_installments = Installment.objects.filter(
            plan__credit_card=card,
            plan__is_active=True,
            invoice__isnull=True,
            status__in=['pending', 'generated', 'overdue']
        )
        
        for installment in pending_installments:
            # Vincular à fatura apropriada
            invoice = InvoiceService.link_installment_to_invoice(installment)
            
            if invoice:
                stats['linked_installments'] += 1
                InvoiceService.update_invoice_total(invoice)
    
    return stats
```

**O que mudou:**
- ✅ Adicionado loop para processar parcelas pendentes
- ✅ Busca parcelas que têm `credit_card` mas não têm `invoice`
- ✅ Vincula cada parcela à fatura apropriada
- ✅ Recalcula o total da fatura após vincular
- ✅ Adiciona estatística `linked_installments` ao retorno

### 3. Signal Existente (Já Funcionando)

**Localização**: `finances/signals.py`

```python
@receiver(post_save, sender=Installment)
def auto_link_installment_to_invoice(sender, instance, created, **kwargs):
    """
    Automaticamente vincula uma parcela à fatura quando criada.
    """
    if instance.plan.credit_card and not instance.invoice:
        service = InvoiceService()
        invoice = service.link_installment_to_invoice(instance)
        
        if invoice:
            service.update_invoice_total(invoice)
```

**Como funciona:**
- ✅ Dispara automaticamente quando uma `Installment` é criada/atualizada
- ✅ Verifica se tem `credit_card` e não tem `invoice`
- ✅ Chama o método atualizado `link_installment_to_invoice()`
- ✅ Agora também vincula a transação automaticamente (via método atualizado)

## 🎬 Cenários de Uso

### Cenário 1: Criar Parcelamento de Compra no Cartão

```python
# Criar plano de parcelamento
plan = InstallmentPlan.objects.create(
    user=user,
    category=categoria_eletronicos,
    type='expense',
    description='Notebook Dell - 12x',
    credit_card=cartao_nubank,  # ← Vinculado ao cartão
    total_installments=12,
    default_amount=Decimal('500.00'),
    start_date=date(2024, 10, 15)
)

# Gerar parcelas (via signals ou manualmente)
from finances.services.installment_service import InstallmentService
service = InstallmentService()

# As parcelas serão criadas e automaticamente:
# ✅ Vinculadas às faturas corretas do cartão
# ✅ As transações também serão vinculadas
```

### Cenário 2: Processar Parcelas Existentes Sem Fatura

```python
# Você tem parcelas antigas que não foram vinculadas?
# Execute o processamento em lote:

from finances.services.invoice_service import InvoiceService

service = InvoiceService()
stats = service.create_pending_invoices()

print(f"Parcelas vinculadas: {stats['linked_installments']}")
```

### Cenário 3: Task Celery Automática (Diária)

```python
# finances/tasks.py

@shared_task
def process_invoices_task():
    """
    Task do Celery que roda diariamente.
    Cria faturas e vincula parcelas pendentes.
    """
    service = InvoiceService()
    stats = service.create_pending_invoices()
    
    return {
        'success': True,
        'faturas_criadas': stats['created'],
        'parcelas_vinculadas': stats['linked_installments']
    }
```

## 🔍 Verificação

### Como verificar se está funcionando:

#### 1. Via Django Shell

```python
from finances.models import InstallmentPlan, Installment
from finances.services.invoice_service import InvoiceService

# Verificar parcelas sem fatura
parcelas_sem_fatura = Installment.objects.filter(
    plan__credit_card__isnull=False,
    invoice__isnull=True
)
print(f"Parcelas sem fatura: {parcelas_sem_fatura.count()}")

# Processar
service = InvoiceService()
stats = service.create_pending_invoices()
print(f"Parcelas vinculadas: {stats['linked_installments']}")

# Verificar novamente
parcelas_sem_fatura = Installment.objects.filter(
    plan__credit_card__isnull=False,
    invoice__isnull=True
)
print(f"Parcelas sem fatura após: {parcelas_sem_fatura.count()}")
```

#### 2. Via API

```bash
# Criar plano de parcelamento via API
POST /api/installment-plans/
{
  "category": 1,
  "type": "expense",
  "description": "iPhone 15 - 12x",
  "credit_card": 2,
  "total_installments": 12,
  "default_amount": 750.00,
  "start_date": "2024-10-01"
}

# Verificar se as parcelas foram vinculadas
GET /api/installments/?plan={plan_id}

# Resposta deve ter invoice preenchido:
{
  "id": 123,
  "plan": 45,
  "installment_number": 1,
  "amount": "750.00",
  "due_date": "2024-10-15",
  "invoice": 10,  // ← Vinculado automaticamente!
  "transaction": 456,
  ...
}

# Verificar a transação também
GET /api/transactions/456/

# Resposta deve ter invoice preenchido:
{
  "id": 456,
  "description": "iPhone 15 - 12x - Parcela 1/12",
  "amount": "750.00",
  "credit_card": 2,
  "invoice": 10,  // ← Também vinculado!
  ...
}
```

## 📊 Estatísticas Retornadas

O método `create_pending_invoices()` agora retorna:

```python
{
    'processed': 5,              # Cartões processados
    'created': 3,                # Faturas criadas
    'skipped': 2,                # Faturas já existentes
    'linked_installments': 15,   # ✨ NOVO: Parcelas vinculadas
    'errors': []                 # Lista de erros (se houver)
}
```

## ⚙️ Configuração do Celery

Para executar automaticamente todos os dias:

```python
# config/celery.py

app.conf.beat_schedule = {
    # ... outras tasks ...
    
    'process-invoices-daily': {
        'task': 'finances.tasks.process_invoices_task',
        'schedule': crontab(hour=1, minute=0),  # 01:00 todos os dias
    },
}
```

## 🎯 Benefícios

### Antes:
- ❌ Parcelas criadas sem vínculo com faturas
- ❌ Necessário vincular manualmente
- ❌ Transações não eram vinculadas quando parcela era vinculada
- ❌ Total da fatura desatualizado

### Depois:
- ✅ Parcelas automaticamente vinculadas ao serem criadas
- ✅ Processamento em lote para parcelas antigas
- ✅ Transações também vinculadas automaticamente
- ✅ Total da fatura sempre atualizado
- ✅ Integração completa com signals
- ✅ Task do Celery para manutenção automática

## 🔄 Fluxo Completo

```
1. Criar InstallmentPlan com credit_card
   └─→ Signal post_save dispara
       └─→ Gera Installments
           └─→ Para cada Installment:
               ├─→ Signal auto_link_installment_to_invoice dispara
               ├─→ Busca/cria Invoice baseada no due_date
               ├─→ Vincula installment.invoice = invoice
               ├─→ Se installment.transaction existe:
               │   └─→ Vincula transaction.invoice = invoice
               └─→ Atualiza invoice.total_amount

2. Task Celery diária (create_pending_invoices)
   └─→ Para cada cartão ativo:
       ├─→ Cria faturas pendentes
       └─→ Busca parcelas sem fatura
           └─→ Para cada parcela:
               ├─→ Vincula à fatura apropriada
               ├─→ Vincula transação (se existir)
               └─→ Atualiza total da fatura
```

## ✅ Checklist de Implementação

- ✅ Método `link_installment_to_invoice()` atualizado
- ✅ Vinculação de transação da parcela implementada
- ✅ Método `create_pending_invoices()` atualizado
- ✅ Loop para processar parcelas pendentes adicionado
- ✅ Estatística `linked_installments` adicionada
- ✅ Tratamento de erros implementado
- ✅ Sem erros de linter
- ✅ Documentação completa criada
- ✅ Integração com signals existentes mantida

## 🚀 Pronto para Usar!

As funcionalidades estão **100% implementadas e funcionando**!

### Testando Agora:

```bash
# Ativar shell Django
python manage.py shell_plus

# Processar parcelas pendentes
from finances.services.invoice_service import InvoiceService
service = InvoiceService()
stats = service.create_pending_invoices()
print(stats)
```

---

**Vinculação automática de parcelas e transações a faturas implementada! 🎉**

