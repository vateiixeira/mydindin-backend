# Exemplos de Uso da API MyDinDin

Este documento contém exemplos práticos de uso da API.

## Autenticação

### 1. Registrar Novo Usuário

**Request:**
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "email": "usuario@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "password": "senha@123",
  "password_confirm": "senha@123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "usuario@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "full_name": "João Silva"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Usuário registrado com sucesso"
}
```

### 2. Login

**Request:**
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "senha@123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "usuario@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "full_name": "João Silva"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Login realizado com sucesso"
}
```

### 3. Renovar Token

**Request:**
```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Obter Perfil

**Request:**
```bash
GET /api/auth/profile/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "id": 1,
  "email": "usuario@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva"
}
```

## Categorias

### 5. Listar Categorias

**Request:**
```bash
GET /api/categories/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "count": 13,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Salário",
      "type": "income",
      "type_display": "Receita",
      "description": "Salário mensal",
      "is_default": true,
      "user": null,
      "user_email": null,
      "transactions_count": 0,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 6. Criar Categoria Personalizada

**Request:**
```bash
POST /api/categories/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "name": "Aplicativos",
  "type": "expense",
  "description": "Assinaturas de aplicativos e serviços digitais"
}
```

**Response:**
```json
{
  "id": 14,
  "name": "Aplicativos",
  "type": "expense",
  "type_display": "Despesa",
  "description": "Assinaturas de aplicativos e serviços digitais",
  "is_default": false,
  "user": 1,
  "user_email": "usuario@example.com",
  "transactions_count": 0,
  "created_at": "2024-10-08T10:30:00Z",
  "updated_at": "2024-10-08T10:30:00Z"
}
```

### 7. Listar Categorias por Tipo

**Request:**
```bash
GET /api/categories/by_type/?type=expense
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Transações

### 8. Criar Transação (Despesa)

**Request:**
```bash
POST /api/transactions/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "category": 5,
  "type": "expense",
  "description": "Aluguel de Outubro",
  "amount": "1500.00",
  "transaction_date": "2024-10-01",
  "due_date": "2024-10-10",
  "status": "pending",
  "is_recurring": true,
  "recurrence": "monthly"
}
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "user_email": "usuario@example.com",
  "category": 5,
  "category_name": "Moradia",
  "type": "expense",
  "type_display": "Despesa",
  "description": "Aluguel de Outubro",
  "amount": "1500.00",
  "transaction_date": "2024-10-01",
  "due_date": "2024-10-10",
  "payment_date": null,
  "is_recurring": true,
  "recurrence": "monthly",
  "recurrence_display": "Mensal",
  "recurrence_end_date": null,
  "status": "pending",
  "status_display": "Pendente",
  "notes": null,
  "created_at": "2024-10-08T10:45:00Z",
  "updated_at": "2024-10-08T10:45:00Z"
}
```

### 9. Criar Transação (Receita)

**Request:**
```bash
POST /api/transactions/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "category": 1,
  "type": "income",
  "description": "Salário Outubro 2024",
  "amount": "5000.00",
  "transaction_date": "2024-10-05",
  "payment_date": "2024-10-05",
  "status": "paid",
  "is_recurring": true,
  "recurrence": "monthly"
}
```

### 10. Listar Transações

**Request:**
```bash
GET /api/transactions/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 11. Filtrar Transações por Período

**Request:**
```bash
GET /api/transactions/by_period/?start_date=2024-10-01&end_date=2024-10-31
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 12. Filtrar Transações por Mês

**Request:**
```bash
GET /api/transactions/by_month/?year=2024&month=10
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 13. Obter Resumo Financeiro

**Request:**
```bash
GET /api/transactions/summary/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "total_incomes": 5000.00,
  "total_expenses": 2500.00,
  "balance": 2500.00,
  "total_transactions": 15,
  "pending_transactions": 3,
  "paid_transactions": 10,
  "overdue_transactions": 2
}
```

### 14. Resumo por Período

**Request:**
```bash
GET /api/transactions/summary/?start_date=2024-10-01&end_date=2024-10-31
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 15. Agrupar por Categoria

**Request:**
```bash
GET /api/transactions/by_category/?type=expense
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
[
  {
    "category": "Moradia",
    "total": 1500.00,
    "count": 1
  },
  {
    "category": "Alimentação",
    "total": 800.00,
    "count": 5
  },
  {
    "category": "Transporte",
    "total": 200.00,
    "count": 8
  }
]
```

### 16. Atualizar Transação

**Request:**
```bash
PUT /api/transactions/1/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "status": "paid",
  "payment_date": "2024-10-08"
}
```

### 17. Deletar Transação

**Request:**
```bash
DELETE /api/transactions/1/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Notas Importantes

1. **Autenticação**: Todos os endpoints (exceto register e login) requerem o header `Authorization: Bearer {token}`

2. **Token Expiration**: O access token expira em 10 dias. Use o refresh token para obter um novo.

3. **Formato de Data**: Use o formato `YYYY-MM-DD` para datas.

4. **Tipos de Transação**: 
   - `income` para receitas
   - `expense` para despesas

5. **Status de Transação**:
   - `pending` - Pendente
   - `paid` - Pago
   - `overdue` - Atrasado

6. **Recorrência**:
   - `none` - Não recorrente
   - `monthly` - Mensal

7. **Categorias**: O sistema já vem com categorias padrão. Você pode criar suas próprias categorias personalizadas.

