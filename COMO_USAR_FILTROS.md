# Como Usar Filtros na API

## Diferença entre SearchFilter e DjangoFilterBackend

### 🔍 SearchFilter (Busca por Texto)
Usado para **buscar texto** dentro dos campos configurados.

**Sintaxe**: `?search=termo`

**Exemplo**:
```
GET /api/transactions/?search=supermercado
```

Busca "supermercado" nos campos: `description`, `notes`, `category__name`

---

### 🎯 DjangoFilterBackend (Filtro por Campos Específicos)
Usado para **filtrar por valores exatos** em campos específicos.

**Sintaxe**: `?campo=valor`

**Exemplos**:

#### Filtrar por tipo de transação
```
GET /api/transactions/?type=income        # Apenas receitas
GET /api/transactions/?type=expense       # Apenas despesas
```

#### Filtrar por status
```
GET /api/transactions/?status=paid        # Apenas pagas
GET /api/transactions/?status=pending     # Apenas pendentes
GET /api/transactions/?status=overdue     # Apenas atrasadas
```

#### Filtrar por categoria
```
GET /api/transactions/?category=5         # Transações da categoria ID 5
```

#### Filtrar por cartão de crédito
```
GET /api/transactions/?credit_card=2      # Transações do cartão ID 2
```

#### Filtrar por fatura
```
GET /api/transactions/?invoice=10         # Transações da fatura ID 10
```

#### Filtrar por período (start_date e end_date)
```
GET /api/transactions/?start_date=2024-01-01&end_date=2024-12-31
# Transações entre 01/01/2024 e 31/12/2024

GET /api/transactions/?start_date=2024-10-01
# Transações a partir de 01/10/2024

GET /api/transactions/?end_date=2024-10-31
# Transações até 31/10/2024
```

---

## 🔥 Combinando Filtros

Você pode combinar múltiplos filtros na mesma requisição:

```
GET /api/transactions/?type=expense&status=paid
# Despesas que já foram pagas

GET /api/transactions/?type=income&search=salário
# Receitas que contêm a palavra "salário"

GET /api/transactions/?category=3&status=pending
# Transações pendentes da categoria 3

GET /api/transactions/?credit_card=1&type=expense
# Despesas do cartão de crédito 1

GET /api/transactions/?start_date=2024-10-01&end_date=2024-10-31&type=expense
# Despesas do mês de outubro de 2024

GET /api/transactions/?start_date=2024-01-01&end_date=2024-12-31&status=paid
# Transações pagas de 2024

GET /api/transactions/?start_date=2024-10-01&type=income&ordering=-amount
# Receitas de outubro ordenadas por valor (maior primeiro)
```

---

## 📊 Ordenação

Use o parâmetro `ordering` para ordenar os resultados:

```
GET /api/transactions/?ordering=transaction_date
# Ordena por data (mais antiga primeiro)

GET /api/transactions/?ordering=-transaction_date
# Ordena por data (mais recente primeiro) - note o "-"

GET /api/transactions/?ordering=-amount
# Ordena por valor (maior primeiro)

GET /api/transactions/?ordering=transaction_date,-amount
# Ordena por data e depois por valor
```

---

## 📋 Campos Disponíveis para Filtro

### TransactionViewSet
- `type` - Tipo: `income` ou `expense`
- `status` - Status: `pending`, `paid`, `overdue`, `cancelled`
- `category` - ID da categoria
- `credit_card` - ID do cartão de crédito
- `invoice` - ID da fatura
- `start_date` - Data inicial (formato: YYYY-MM-DD) - filtra `transaction_date >= start_date`
- `end_date` - Data final (formato: YYYY-MM-DD) - filtra `transaction_date <= end_date`

**Busca**: `description`, `notes`, `category__name`

**Ordenação**: `transaction_date`, `amount`, `created_at`

---

## 🎯 Exemplos Práticos

### 1. Ver todas as despesas não pagas
```
GET /api/transactions/?type=expense&status=pending
```

### 2. Ver transações do mês de outubro de 2024
```
GET /api/transactions/?start_date=2024-10-01&end_date=2024-10-31
```

### 3. Ver receitas do último trimestre
```
GET /api/transactions/?start_date=2024-07-01&end_date=2024-09-30&type=income
```

### 4. Ver gastos em um cartão específico no mês atual
```
GET /api/transactions/?credit_card=1&type=expense&start_date=2024-10-01&end_date=2024-10-31&ordering=-transaction_date
```

### 5. Buscar transações de mercado não pagas em um período
```
GET /api/transactions/?search=mercado&status=pending&start_date=2024-10-01&end_date=2024-10-31
```

### 6. Ver todas as despesas pagas de 2024
```
GET /api/transactions/?type=expense&status=paid&start_date=2024-01-01&end_date=2024-12-31
```

---

## 🔄 Endpoints Customizados (Ainda Disponíveis)

Além dos filtros, você ainda pode usar os endpoints customizados:

```
GET /api/transactions/by_period/?start_date=2024-01-01&end_date=2024-12-31
GET /api/transactions/by_month/?year=2024&month=10
GET /api/transactions/summary/
GET /api/transactions/by_category/?type=expense
```

---

## 💡 Dicas

1. **Combine filtros** para buscas mais específicas
2. Use `search` para buscar texto livre
3. Use filtros de campo (`type`, `status`, etc) para valores exatos
4. Use `ordering` para ordenar resultados
5. O `-` antes do campo em `ordering` inverte a ordem (desc)
6. Todos os filtros respeitam o usuário logado automaticamente

---

## 🚀 Testando

### Com curl:
```bash
curl -H "Authorization: Bearer SEU_TOKEN" \
  "http://localhost:8000/api/transactions/?type=income&status=paid"
```

### Com Postman/Insomnia:
```
URL: http://localhost:8000/api/transactions/
Params:
  - type: income
  - status: paid
Header:
  - Authorization: Bearer SEU_TOKEN
```

### Com JavaScript (fetch):
```javascript
const params = new URLSearchParams({
  type: 'expense',
  status: 'pending',
  ordering: '-transaction_date'
});

fetch(`http://localhost:8000/api/transactions/?${params}`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

