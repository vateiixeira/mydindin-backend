# Sincronização Automática de Valores: Parcelas e Transações

## 📋 Funcionalidade Implementada

Quando você atualizar o valor (`amount`) de uma **parcela** (installment) através de um PATCH, o sistema automaticamente sincroniza o valor da **transação** vinculada (se existir).

## 🎯 Como Funciona

### Fluxo Automático

1. **Você faz um PATCH** na parcela:
   ```
   PATCH /api/installments/66/
   {
     "amount": 350.00
   }
   ```

2. **O sistema verifica**:
   - ✅ O valor mudou?
   - ✅ Existe uma transação vinculada?
   - ✅ Existe uma fatura vinculada?

3. **O sistema atualiza automaticamente**:
   - 🔄 Atualiza o `amount` da parcela
   - 🔄 Atualiza o `amount` da transação vinculada
   - 🔄 Recalcula o total da fatura (se vinculada)

## 💡 Exemplos Práticos

### Exemplo 1: Parcela com Transação Vinculada

**Situação**: Você criou uma parcela de um financiamento e o sistema já gerou a transação automaticamente.

```bash
# Estado inicial
Parcela #66:
  amount: 300.00
  transaction_id: 150

Transaction #150:
  amount: 300.00

# Você atualiza a parcela
PATCH /api/installments/66/
{
  "amount": 350.00
}

# Estado final (automático)
Parcela #66:
  amount: 350.00  ← Atualizado
  transaction_id: 150

Transaction #150:
  amount: 350.00  ← Atualizado automaticamente!
```

### Exemplo 2: Parcela com Transação E Fatura

**Situação**: Parcela de um cartão de crédito vinculada a uma fatura.

```bash
# Estado inicial
Parcela #66:
  amount: 500.00
  transaction_id: 150
  invoice_id: 10

Transaction #150:
  amount: 500.00

Invoice #10:
  total_amount: 2000.00

# Você atualiza a parcela
PATCH /api/installments/66/
{
  "amount": 600.00
}

# Estado final (automático)
Parcela #66:
  amount: 600.00  ← Atualizado
  transaction_id: 150
  invoice_id: 10

Transaction #150:
  amount: 600.00  ← Atualizado automaticamente!

Invoice #10:
  total_amount: 2100.00  ← Recalculado automaticamente!
```

### Exemplo 3: Parcela SEM Transação

**Situação**: Parcela ainda pendente, sem transação gerada.

```bash
# Estado inicial
Parcela #66:
  amount: 300.00
  transaction_id: null
  status: pending

# Você atualiza a parcela
PATCH /api/installments/66/
{
  "amount": 350.00
}

# Estado final
Parcela #66:
  amount: 350.00  ← Atualizado
  transaction_id: null
  status: pending

# Nada mais é atualizado (não há transação para sincronizar)
```

## 🔧 Campos que Podem Ser Atualizados

Você pode atualizar outros campos da parcela além do `amount`:

```bash
PATCH /api/installments/66/
{
  "amount": 350.00,           # ← Sincroniza com a transação
  "due_date": "2024-11-15",   # Apenas atualiza a parcela
  "status": "paid",           # Apenas atualiza a parcela
  "notes": "Ajuste de valor"  # Apenas atualiza a parcela
}
```

⚠️ **Importante**: Apenas o campo `amount` é sincronizado com a transação!

## 🛠️ Implementação Técnica

### Localização do Código

O código está implementado em:
```
finances/views.py
  └── InstallmentViewSet
      └── perform_update()  # Método que faz a sincronização
```

### Lógica Implementada

```python
def perform_update(self, serializer):
    # 1. Captura o valor antigo
    old_amount = installment.amount
    
    # 2. Salva a parcela com os novos dados
    updated_installment = serializer.save()
    
    # 3. Se o amount mudou E existe transação vinculada
    if new_amount != old_amount and updated_installment.transaction:
        # Atualiza o amount da transação
        transaction.amount = new_amount
        transaction.save()
        
        # Se existe fatura vinculada, recalcula o total
        if updated_installment.invoice:
            InvoiceService.update_invoice_total(invoice)
```

## 🎯 Casos de Uso

### 1. Ajuste de Valor de Parcela
```bash
# O valor da parcela do financiamento estava errado
PATCH /api/installments/66/
{
  "amount": 1500.00  # Corrige de 1450.00 para 1500.00
}
# ✅ Transação automaticamente atualizada para 1500.00
```

### 2. Reajuste de Parcela de Cartão
```bash
# A parcela do cartão teve um acréscimo de juros
PATCH /api/installments/66/
{
  "amount": 550.00  # Era 500.00, agora com juros
}
# ✅ Transação atualizada para 550.00
# ✅ Fatura recalculada com o novo total
```

### 3. Correção de Lançamento
```bash
# Você lançou o valor errado
PATCH /api/installments/66/
{
  "amount": 320.50  # Corrige valor digitado errado
}
# ✅ Tudo sincronizado automaticamente
```

## ⚙️ Configuração

### Não há configuração necessária!

A funcionalidade está **ativa por padrão** para todos os PATCH em `/api/installments/{id}/`.

## 🧪 Testando

### Com curl:
```bash
# 1. Ver o estado atual
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/installments/66/

# 2. Atualizar o amount
curl -X PATCH \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 350.00}' \
  http://localhost:8000/api/installments/66/

# 3. Verificar a transação vinculada (se tiver)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/transactions/150/
# O amount deve estar sincronizado!
```

### Com JavaScript (fetch):
```javascript
// Atualizar parcela
const response = await fetch('http://localhost:8000/api/installments/66/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    amount: 350.00
  })
});

const installment = await response.json();
console.log('Parcela atualizada:', installment);

// Se tiver transaction_id, pode buscar para confirmar
if (installment.transaction) {
  const txResponse = await fetch(
    `http://localhost:8000/api/transactions/${installment.transaction}/`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  const transaction = await txResponse.json();
  console.log('Transação sincronizada:', transaction.amount);
  // amount deve ser igual ao da parcela!
}
```

## 🔍 Verificando a Sincronização

### Passo a Passo:

1. **Liste as parcelas**:
   ```bash
   GET /api/installments/
   ```

2. **Identifique uma parcela com transaction_id preenchido**:
   ```json
   {
     "id": 66,
     "amount": "300.00",
     "transaction": 150,  ← Tem transação vinculada
     ...
   }
   ```

3. **Atualize o amount**:
   ```bash
   PATCH /api/installments/66/
   {
     "amount": 350.00
   }
   ```

4. **Verifique a transação**:
   ```bash
   GET /api/transactions/150/
   ```
   
   Deve retornar:
   ```json
   {
     "id": 150,
     "amount": "350.00",  ← Sincronizado automaticamente!
     ...
   }
   ```

## ✅ Benefícios

- ✅ **Integridade de Dados**: Parcela e transação sempre com valores consistentes
- ✅ **Menos Erros**: Não precisa atualizar manualmente em dois lugares
- ✅ **Automático**: Funciona sem configuração adicional
- ✅ **Seguro**: Só atualiza se o valor realmente mudou
- ✅ **Completo**: Recalcula faturas automaticamente quando necessário

## ⚠️ Observações Importantes

1. **Apenas o campo `amount` é sincronizado** - outros campos (status, due_date, etc) não afetam a transação

2. **A sincronização só acontece se existir uma transação vinculada** - se `transaction_id` for `null`, nada é feito

3. **O recálculo da fatura só acontece se a parcela estiver vinculada a uma fatura** - caso contrário, só a transação é atualizada

4. **O valor da fatura pode não mudar se o novo total declarado for menor que o total manual** - o `InvoiceService.update_invoice_total()` preserva valores manuais maiores

## 🚀 Próximos Passos

Se você quiser estender essa funcionalidade:

1. **Sincronizar outros campos** (ex: status, due_date)
2. **Adicionar logs** para rastrear mudanças
3. **Criar notificações** quando valores forem sincronizados
4. **Adicionar validações** adicionais antes de sincronizar

---

**Desenvolvido para garantir integridade entre parcelas, transações e faturas! 🎯**

