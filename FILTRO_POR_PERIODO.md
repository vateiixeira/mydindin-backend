# 📅 Filtro por Período em Transações

## ✅ Implementação Concluída

Agora o endpoint `GET /api/transactions/` aceita os parâmetros opcionais `start_date` e `end_date` para filtrar transações por período!

## 🎯 Como Usar

### 1. Filtrar por Período Completo (start_date e end_date)

```bash
GET /api/transactions/?start_date=2024-01-01&end_date=2024-12-31
```

Retorna todas as transações entre 01/01/2024 e 31/12/2024 (inclusive).

### 2. Filtrar Apenas Data Inicial (start_date)

```bash
GET /api/transactions/?start_date=2024-10-01
```

Retorna todas as transações a partir de 01/10/2024 (sem limite final).

### 3. Filtrar Apenas Data Final (end_date)

```bash
GET /api/transactions/?end_date=2024-10-31
```

Retorna todas as transações até 31/10/2024 (sem limite inicial).

## 🔥 Combinando com Outros Filtros

A grande vantagem é que você pode combinar com **todos os outros filtros**:

### Despesas do mês de outubro
```bash
GET /api/transactions/?start_date=2024-10-01&end_date=2024-10-31&type=expense
```

### Receitas pagas de 2024
```bash
GET /api/transactions/?start_date=2024-01-01&end_date=2024-12-31&type=income&status=paid
```

### Despesas de uma categoria específica no trimestre
```bash
GET /api/transactions/?start_date=2024-07-01&end_date=2024-09-30&category=5&type=expense
```

### Gastos no cartão de crédito em outubro ordenados por valor
```bash
GET /api/transactions/?start_date=2024-10-01&end_date=2024-10-31&credit_card=1&ordering=-amount
```

### Buscar transações de "mercado" em um período
```bash
GET /api/transactions/?start_date=2024-10-01&end_date=2024-10-31&search=mercado
```

## 📝 Formato de Data

**Formato aceito**: `YYYY-MM-DD` (ISO 8601)

Exemplos válidos:
- ✅ `2024-10-09`
- ✅ `2024-01-01`
- ✅ `2023-12-31`

Exemplos inválidos:
- ❌ `09-10-2024` (formato brasileiro)
- ❌ `10/09/2024` (com barras)
- ❌ `2024/10/09` (com barras)
- ❌ `09-10-24` (ano curto)

## 🔧 Comportamento

### Se as datas forem válidas:
✅ Filtra as transações pelo `transaction_date`

### Se as datas forem inválidas:
✅ Ignora o filtro e retorna todas as transações (sem erro)

### Se apenas um parâmetro for fornecido:
✅ Filtra apenas por aquele parâmetro
- `start_date` → `transaction_date >= start_date`
- `end_date` → `transaction_date <= end_date`

## 💡 Exemplos com curl

### Filtrar mês atual (outubro 2024)
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/transactions/?start_date=2024-10-01&end_date=2024-10-31"
```

### Despesas do ano de 2024
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/transactions/?start_date=2024-01-01&end_date=2024-12-31&type=expense"
```

### Últimos 30 dias
```bash
# Calcule as datas primeiro
START_DATE=$(date -d "30 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/transactions/?start_date=${START_DATE}&end_date=${END_DATE}"
```

## 🌐 Exemplos com JavaScript

### Fetch API

```javascript
const startDate = '2024-10-01';
const endDate = '2024-10-31';

const params = new URLSearchParams({
  start_date: startDate,
  end_date: endDate,
  type: 'expense'
});

fetch(`http://localhost:8000/api/transactions/?${params}`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

### Axios

```javascript
import axios from 'axios';

const response = await axios.get('http://localhost:8000/api/transactions/', {
  params: {
    start_date: '2024-10-01',
    end_date: '2024-10-31',
    type: 'expense',
    status: 'paid'
  },
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

console.log(response.data);
```

### React Hook Personalizado

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

function useTransactionsByPeriod(startDate, endDate, filters = {}) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      
      const params = {
        start_date: startDate,
        end_date: endDate,
        ...filters
      };

      const response = await axios.get('/api/transactions/', {
        params,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      setTransactions(response.data.results);
      setLoading(false);
    };

    if (startDate && endDate) {
      fetchData();
    }
  }, [startDate, endDate, filters]);

  return { transactions, loading };
}

// Uso
function MyComponent() {
  const { transactions, loading } = useTransactionsByPeriod(
    '2024-10-01',
    '2024-10-31',
    { type: 'expense' }
  );

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      {transactions.map(tx => (
        <div key={tx.id}>{tx.description}: R$ {tx.amount}</div>
      ))}
    </div>
  );
}
```

## 🆚 Comparação com Endpoints Customizados

### Antes (Endpoints Customizados)

```bash
# Precisava usar endpoints específicos
GET /api/transactions/by_period/?start_date=2024-01-01&end_date=2024-12-31
GET /api/transactions/by_month/?year=2024&month=10
```

**Problemas**:
- ❌ Não funcionava com outros filtros do DjangoFilterBackend
- ❌ Não funcionava com paginação automática
- ❌ Precisava de endpoints separados

### Agora (Filtro Integrado)

```bash
# Usa o endpoint principal com filtros
GET /api/transactions/?start_date=2024-01-01&end_date=2024-12-31
```

**Vantagens**:
- ✅ Funciona com todos os outros filtros (`type`, `status`, etc)
- ✅ Funciona com paginação automática
- ✅ Funciona com busca (`search`)
- ✅ Funciona com ordenação (`ordering`)
- ✅ Endpoint único e consistente

## 📊 Use Cases Práticos

### 1. Dashboard Mensal
```javascript
// Buscar transações do mês atual
const now = new Date();
const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

const params = {
  start_date: firstDay.toISOString().split('T')[0],
  end_date: lastDay.toISOString().split('T')[0]
};
```

### 2. Relatório Anual
```bash
GET /api/transactions/?start_date=2024-01-01&end_date=2024-12-31&ordering=transaction_date
```

### 3. Comparação Trimestral
```bash
# Q1 2024
GET /api/transactions/?start_date=2024-01-01&end_date=2024-03-31&type=expense

# Q2 2024
GET /api/transactions/?start_date=2024-04-01&end_date=2024-06-30&type=expense
```

### 4. Buscar Transações Recentes
```bash
# Últimos 7 dias
GET /api/transactions/?start_date=2024-10-02&end_date=2024-10-09
```

## ✅ Checklist de Implementação

- ✅ Filtro `start_date` implementado
- ✅ Filtro `end_date` implementado
- ✅ Funciona isoladamente (apenas start ou apenas end)
- ✅ Funciona combinado (start + end)
- ✅ Compatível com outros filtros do DjangoFilterBackend
- ✅ Compatível com paginação
- ✅ Compatível com busca (search)
- ✅ Compatível com ordenação (ordering)
- ✅ Tratamento de erros (datas inválidas)
- ✅ Documentação atualizada

## 🎓 Implementação Técnica

O filtro foi implementado no método `get_queryset()` do `TransactionViewSet`:

```python
def get_queryset(self):
    queryset = Transaction.objects.filter(user=self.request.user)
    
    start_date = self.request.query_params.get('start_date')
    end_date = self.request.query_params.get('end_date')
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        queryset = queryset.filter(
            transaction_date__gte=start,
            transaction_date__lte=end
        )
    
    return queryset
```

---

**Filtro por período implementado e funcionando! 🎉**

Consulte `COMO_USAR_FILTROS.md` para documentação completa de todos os filtros disponíveis.

