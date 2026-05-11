# 🐛 Correção: RelatedObjectDoesNotExist em Transaction.installment

## 🔴 Erro Encontrado

```python
RelatedObjectDoesNotExist at /api/transactions/
Transaction has no installment.
```

### Localização do Erro:
```python
# finances/models.py - Transaction.save()
if self.installment:  # ← ERRO AQUI!
    ^^^^^^^^^^^^^^^^
    self.installment.status = self.status
```

## 🔍 Causa Raiz

### Estrutura do Relacionamento:

```python
# Model Installment
class Installment(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installment'  # ← Relacionamento reverso
    )

# Model Transaction
class Transaction(models.Model):
    # Não tem campo 'installment' direto
    # Mas tem acesso via relacionamento reverso
    pass
```

### O Problema:

Quando você acessa `transaction.installment` em uma transação que **não** tem uma parcela vinculada, o Django lança `Transaction.installment.RelatedObjectDoesNotExist`.

Isso acontece porque:
1. ✅ Nem toda `Transaction` tem uma `Installment` vinculada
2. ✅ Transações normais (não parceladas) não têm installment
3. ❌ O código estava tentando acessar `self.installment` sem verificar se existe

### Cenários:

```python
# Cenário 1: Transação com parcela ✅
transaction = Transaction.objects.get(id=1)
transaction.installment  # ✅ OK - tem parcela vinculada

# Cenário 2: Transação sem parcela ❌
transaction = Transaction.objects.get(id=2)
transaction.installment  # ❌ ERRO - RelatedObjectDoesNotExist!
```

## ✅ Solução Implementada

Usar `try/except` para capturar a exceção:

### ❌ Código Antigo (Com Bug):

```python
def save(self, *args, **kwargs):
    # ...
    
    # Atualizar status da transação
    if self.installment:  # ← Lança exceção se não existir!
        self.installment.status = self.status
        self.installment.save()
    
    super().save(*args, **kwargs)
```

### ✅ Código Novo (Corrigido):

```python
def save(self, *args, **kwargs):
    # ...
    
    # Atualizar status da parcela vinculada (se existir)
    try:
        if self.installment:
            self.installment.status = self.status
            self.installment.save()
    except Installment.DoesNotExist:
        # Transação não está vinculada a nenhuma parcela
        pass
    
    super().save(*args, **kwargs)
```

## 🎯 Como Funciona Agora

### Fluxo de Salvamento:

```python
# 1. Salvar transação com parcela vinculada
transaction_with_installment = Transaction.objects.get(id=1)
transaction_with_installment.status = 'paid'
transaction_with_installment.save()
# ✅ Sincroniza status com a parcela
# ✅ installment.status também vira 'paid'

# 2. Salvar transação sem parcela vinculada
normal_transaction = Transaction.objects.get(id=2)
normal_transaction.status = 'paid'
normal_transaction.save()
# ✅ Salva normalmente
# ✅ Não lança erro
# ✅ Apenas ignora a tentativa de sincronizar parcela
```

## 🔧 Abordagens Alternativas

### Abordagem 1: hasattr() (❌ Não funciona bem)

```python
# NÃO recomendado para OneToOneField
if hasattr(self, 'installment') and self.installment:
    # hasattr vai tentar acessar e ainda vai lançar exceção
```

**Problema**: `hasattr()` vai tentar acessar o atributo e vai lançar a mesma exceção!

### Abordagem 2: getattr() com default (⚠️ Funciona mas menos claro)

```python
installment = getattr(self, 'installment', None)
if installment:
    installment.status = self.status
    installment.save()
```

**Problema**: Ainda pode lançar exceção ao acessar o atributo.

### Abordagem 3: try/except (✅ Melhor - Implementada)

```python
try:
    if self.installment:
        self.installment.status = self.status
        self.installment.save()
except Installment.DoesNotExist:
    pass
```

**Vantagens**:
- ✅ Explícito e claro
- ✅ É o padrão recomendado pelo Django
- ✅ Lida corretamente com OneToOneField
- ✅ Fácil de entender

## 📊 Quando o Erro Acontecia

### Endpoints Afetados:

```bash
# Qualquer operação que salvasse uma Transaction sem parcela:

# 1. Criar transação normal
POST /api/transactions/
{
  "type": "expense",
  "description": "Supermercado",
  "amount": 150.00,
  ...
}
# ❌ ERRO! (antes da correção)

# 2. Atualizar transação normal
PATCH /api/transactions/123/
{
  "status": "paid"
}
# ❌ ERRO! (antes da correção)

# 3. Listar transações (trigger save via signals)
GET /api/transactions/
# ❌ ERRO! (se algum signal salvasse)
```

### Transações Afetadas:

- ❌ Transações normais (sem parcelamento)
- ❌ Transações de receita simples
- ❌ Transações de despesa simples
- ❌ Transações recorrentes (sem installment)
- ✅ Transações com parcelas vinculadas (funcionavam)

## 🧪 Como Testar

### Teste 1: Criar transação normal

```bash
# Deve funcionar sem erro
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": 1,
    "type": "expense",
    "description": "Supermercado",
    "amount": 150.00,
    "transaction_date": "2024-10-09"
  }' \
  http://localhost:8000/api/transactions/
```

**Resultado esperado**: ✅ Transação criada com sucesso

### Teste 2: Atualizar status de transação normal

```bash
# Deve funcionar sem erro
curl -X PATCH \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "paid"}' \
  http://localhost:8000/api/transactions/123/
```

**Resultado esperado**: ✅ Status atualizado com sucesso

### Teste 3: Atualizar transação com parcela

```bash
# Deve funcionar E sincronizar com a parcela
curl -X PATCH \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "paid"}' \
  http://localhost:8000/api/transactions/456/  # tem parcela vinculada
```

**Resultado esperado**: 
- ✅ Status da transação atualizado
- ✅ Status da parcela sincronizado

### Teste 4: Via Django Shell

```python
from finances.models import Transaction

# Teste 1: Transação sem parcela
tx = Transaction.objects.create(
    user=user,
    category=category,
    type='expense',
    description='Teste',
    amount=100.00,
    transaction_date=date.today()
)
# ✅ Deve criar sem erro

# Teste 2: Atualizar status
tx.status = 'paid'
tx.save()
# ✅ Deve salvar sem erro

print("Tudo funcionando! ✅")
```

## ✅ Checklist da Correção

- ✅ Erro identificado (RelatedObjectDoesNotExist)
- ✅ Causa raiz encontrada (acesso direto a OneToOneField)
- ✅ Solução implementada (try/except)
- ✅ Sem erros de linter
- ✅ Testado com transações normais
- ✅ Testado com transações com parcelas
- ✅ Documentação criada

## 🎓 Boas Práticas para OneToOneField

### Quando acessar relacionamento reverso OneToOne:

```python
# ✅ CERTO - Sempre use try/except
try:
    related_object = obj.related_name
    # fazer algo com related_object
except RelatedModel.DoesNotExist:
    # lidar com caso não existir
    pass

# ❌ ERRADO - Acesso direto
if obj.related_name:  # Lança exceção se não existir!
    pass
```

### Verificar se existe:

```python
# Opção 1: try/except (melhor)
try:
    related = obj.related_name
    has_related = True
except RelatedModel.DoesNotExist:
    has_related = False

# Opção 2: Verificar no banco
from django.core.exceptions import ObjectDoesNotExist
try:
    obj.related_name
    has_related = True
except ObjectDoesNotExist:
    has_related = False
```

## 📚 Referências

- [Django OneToOneField](https://docs.djangoproject.com/en/stable/ref/models/fields/#onetoonefield)
- [Django RelatedObjectDoesNotExist](https://docs.djangoproject.com/en/stable/ref/exceptions/#django.core.exceptions.ObjectDoesNotExist)
- [Django Model.DoesNotExist](https://docs.djangoproject.com/en/stable/ref/models/instances/#django.db.models.Model.DoesNotExist)

---

**Erro corrigido! Transações agora podem ser salvas sem parcela vinculada! ✅**

