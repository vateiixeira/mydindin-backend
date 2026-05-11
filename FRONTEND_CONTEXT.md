# 📱 MyDinDin - Contexto Completo para Desenvolvimento Frontend

Este documento contém todas as informações necessárias para desenvolver o frontend da aplicação MyDinDin - um sistema completo de gestão financeira pessoal com suporte a transações recorrentes e parcelamento.

---

## 📋 Índice

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Autenticação e Autorização](#autenticação-e-autorização)
3. [Modelos de Dados](#modelos-de-dados)
4. [Endpoints da API](#endpoints-da-api)
5. [Fluxos de Usuário](#fluxos-de-usuário)
6. [Regras de Negócio](#regras-de-negócio)
7. [Exemplos de Requisições e Respostas](#exemplos-de-requisições-e-respostas)
8. [Requisitos do Frontend](#requisitos-do-frontend)

---

## 🎯 Visão Geral do Projeto

### O que é o MyDinDin?

MyDinDin é uma aplicação de gestão financeira pessoal que permite:
- ✅ Controle de receitas e despesas
- ✅ Categorização de transações
- ✅ **Transações recorrentes automáticas** (salários, aluguéis, assinaturas)
- ✅ **Gestão de parcelamentos** (consórcios, financiamentos, compras parceladas)
- ✅ Relatórios e resumos financeiros
- ✅ Filtros por período, categoria e tipo

### Tecnologias do Backend

- **Django 5.1.2** + **Django REST Framework**
- **PostgreSQL** (banco de dados)
- **JWT** (autenticação)
- **Celery + Redis** (automação de tarefas)
- **CORS habilitado** para frontend

### URL Base da API

```
http://localhost:8000/api/
```

---

## 🔐 Autenticação e Autorização

### Sistema de Autenticação

O sistema usa **JWT (JSON Web Tokens)** para autenticação.

### Endpoints de Autenticação

#### 1. Registro de Usuário

```http
POST /api/accounts/register/
Content-Type: application/json

{
  "email": "usuario@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "password": "senha123",
  "password_confirm": "senha123"
}
```

**Resposta (201 Created):**
```json
{
  "id": 1,
  "email": "usuario@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva"
}
```

#### 2. Login

```http
POST /api/accounts/login/
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "senha123"
}
```

**Resposta (200 OK):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 3. Refresh Token

```http
POST /api/accounts/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Resposta (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 4. Logout

```http
POST /api/accounts/logout/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 5. Perfil do Usuário

```http
GET /api/accounts/profile/
Authorization: Bearer {access_token}
```

**Resposta:**
```json
{
  "id": 1,
  "email": "usuario@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva"
}
```

### Como Usar JWT no Frontend

Todas as requisições autenticadas devem incluir o header:

```
Authorization: Bearer {access_token}
```

O **access token** expira em **10 dias**.  
O **refresh token** expira em **30 dias**.

---

## 📊 Modelos de Dados

### 1. User (Usuário)

```typescript
interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string; // read-only
}
```

### 2. Category (Categoria)

```typescript
interface Category {
  id: number;
  name: string;
  type: 'income' | 'expense';
  type_display: string; // "Receita" ou "Despesa"
  description?: string;
  is_default: boolean;
  user?: number | null; // read-only - automaticamente preenchido com usuário logado
  user_email?: string; // read-only
  transactions_count: number; // read-only
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}
```

**Nota:** O campo `user` é preenchido automaticamente com o usuário logado. Não é necessário enviá-lo na criação.

**Categorias Padrão do Sistema:**

**Receitas:**
- Salário
- Freelance
- Investimentos
- Outros Ganhos

**Despesas:**
- Alimentação
- Transporte
- Moradia
- Saúde
- Educação
- Lazer
- Contas
- Outros Gastos

### 3. Transaction (Transação)

```typescript
interface Transaction {
  id: number;
  user: number; // read-only - automaticamente preenchido com usuário logado
  user_email: string; // read-only
  category: number;
  category_name: string; // read-only
  type: 'income' | 'expense';
  type_display: string; // read-only
  description: string;
  amount: string; // decimal como string "1500.00"
  transaction_date: string; // YYYY-MM-DD
  due_date?: string | null; // YYYY-MM-DD
  payment_date?: string | null; // YYYY-MM-DD
  is_recurring: boolean;
  recurrence: 'none' | 'monthly';
  recurrence_display: string; // read-only
  recurrence_end_date?: string | null; // YYYY-MM-DD
  status: 'pending' | 'paid' | 'overdue';
  status_display: string; // read-only
  notes?: string;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}
```

**Nota:** O campo `user` é preenchido automaticamente com o usuário logado. Não é necessário enviá-lo na criação.

### 4. RecurringTemplate (Template Recorrente)

```typescript
interface RecurringTemplate {
  id: number;
  user: number; // read-only - automaticamente preenchido com usuário logado
  user_email: string; // read-only
  category: number;
  category_name: string; // read-only
  type: 'income' | 'expense';
  type_display: string; // read-only
  description: string;
  amount: string; // decimal "5000.00"
  day_of_month: number; // 1-31
  is_active: boolean;
  start_date: string; // YYYY-MM-DD
  end_date?: string | null; // YYYY-MM-DD
  last_generated_date?: string | null; // YYYY-MM-DD, read-only
  notes?: string;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}
```

**Nota:** O campo `user` é preenchido automaticamente com o usuário logado. Não é necessário enviá-lo na criação.

**Comportamento:**
- Celery cria transação automaticamente todo dia configurado (00:01)
- Só cria se `is_active = true`
- Só cria uma vez por mês
- Respeita `start_date` e `end_date`

### 5. InstallmentPlan (Plano de Parcelamento)

```typescript
interface InstallmentPlan {
  id: number;
  user: number; // read-only - automaticamente preenchido com usuário logado
  user_email: string; // read-only
  category: number;
  category_name: string; // read-only
  type: 'income' | 'expense';
  type_display: string; // read-only
  description: string;
  total_installments: number;
  default_amount: string; // decimal "500.00"
  start_date: string; // YYYY-MM-DD (primeira parcela)
  is_active: boolean;
  notes?: string;
  installments_count: number; // read-only
  paid_installments_count: number; // read-only
  total_amount: string; // read-only, soma de todas parcelas
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}
```

**Nota:** O campo `user` é preenchido automaticamente com o usuário logado. Não é necessário enviá-lo na criação.

**Comportamento:**
- Ao criar, gera automaticamente todas as parcelas
- Parcelas têm vencimento mensal
- Cada parcela pode ter valor individual

### 6. Installment (Parcela)

```typescript
interface Installment {
  id: number;
  plan: number;
  plan_description: string; // read-only
  installment_number: number; // 1, 2, 3...
  amount: string; // decimal "500.00"
  due_date: string; // YYYY-MM-DD
  status: 'pending' | 'generated' | 'paid' | 'overdue';
  status_display: string; // read-only
  transaction?: number | null; // read-only
  transaction_description?: string | null; // read-only
  notes?: string;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}
```

**Comportamento:**
- Celery cria transação 7 dias antes do vencimento (00:05)
- Status muda para `generated` quando transação é criada
- Status muda para `overdue` se vencer sem pagar

---

## 🌐 Endpoints da API

### Base URL
```
http://localhost:8000/api/
```

### 📁 Categories

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/categories/` | Listar categorias (padrão + usuário) |
| POST | `/categories/` | Criar categoria personalizada |
| GET | `/categories/{id}/` | Detalhe da categoria |
| PUT | `/categories/{id}/` | Atualizar categoria |
| DELETE | `/categories/{id}/` | Deletar categoria |
| GET | `/categories/by_type/?type=income` | Filtrar por tipo |

### 💰 Transactions

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/transactions/` | Listar transações (paginado) |
| POST | `/transactions/` | Criar transação |
| GET | `/transactions/{id}/` | Detalhe da transação |
| PUT | `/transactions/{id}/` | Atualizar transação |
| DELETE | `/transactions/{id}/` | Deletar transação |
| GET | `/transactions/by_period/?start_date=2025-01-01&end_date=2025-12-31` | Filtrar por período |
| GET | `/transactions/by_month/?year=2025&month=10` | Filtrar por mês |
| GET | `/transactions/summary/` | Resumo financeiro |
| GET | `/transactions/summary/?start_date=2025-01-01&end_date=2025-12-31` | Resumo por período |
| GET | `/transactions/by_category/?type=expense` | Agrupar por categoria |

### 🔄 Recurring Templates

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/recurring-templates/` | Listar templates |
| POST | `/recurring-templates/` | Criar template |
| GET | `/recurring-templates/{id}/` | Detalhe |
| PUT | `/recurring-templates/{id}/` | Atualizar |
| DELETE | `/recurring-templates/{id}/` | Deletar |
| POST | `/recurring-templates/{id}/pause/` | Pausar template |
| POST | `/recurring-templates/{id}/resume/` | Retomar template |
| POST | `/recurring-templates/{id}/generate_now/` | Gerar transação agora |
| GET | `/recurring-templates/active/` | Listar só ativos |

### 📦 Installment Plans

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/installment-plans/` | Listar planos |
| POST | `/installment-plans/` | Criar plano |
| GET | `/installment-plans/{id}/` | Detalhe (com parcelas) |
| PUT | `/installment-plans/{id}/` | Atualizar |
| DELETE | `/installment-plans/{id}/` | Deletar |
| GET | `/installment-plans/{id}/installments/` | Listar parcelas |
| GET | `/installment-plans/{id}/pending_installments/` | Parcelas pendentes |
| GET | `/installment-plans/{id}/summary/` | Resumo do plano |

### 📋 Installments

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/installments/` | Listar parcelas |
| GET | `/installments/{id}/` | Detalhe |
| PUT | `/installments/{id}/` | Atualizar |
| GET | `/installments/upcoming/?days=30` | Próximas a vencer |
| GET | `/installments/overdue/` | Atrasadas |
| POST | `/installments/{id}/mark_paid/` | Marcar como pago |

---

## 🎨 Fluxos de Usuário

### Fluxo 1: Registro e Login

```mermaid
1. Usuário acessa página de registro
2. Preenche: email, nome, sobrenome, senha
3. POST /api/accounts/register/
4. Redireciona para login
5. Usuário faz login
6. POST /api/accounts/login/
7. Recebe access_token e refresh_token
8. Armazena tokens (localStorage/sessionStorage)
9. Redireciona para dashboard
```

### Fluxo 2: Dashboard Inicial

```mermaid
1. GET /api/transactions/summary/ - Pega resumo financeiro
2. GET /api/transactions/?page=1 - Lista últimas transações
3. GET /api/installments/upcoming/?days=7 - Próximas parcelas a vencer
4. Exibe:
   - Saldo total
   - Receitas do mês
   - Despesas do mês
   - Transações pendentes
   - Parcelas próximas
```

### Fluxo 3: Criar Transação Manual

```mermaid
1. Usuário clica "Nova Transação"
2. GET /api/categories/ - Carrega categorias
3. Usuário preenche formulário:
   - Tipo (receita/despesa)
   - Categoria
   - Descrição
   - Valor
   - Data
   - Status
4. POST /api/transactions/
5. Atualiza lista de transações
6. Atualiza resumo
```

### Fluxo 4: Criar Salário Recorrente

```mermaid
1. Usuário acessa "Transações Recorrentes"
2. Clica "Novo Template"
3. GET /api/categories/?type=income
4. Preenche:
   - Categoria: "Salário"
   - Descrição: "Salário CLT"
   - Valor: R$ 5.000,00
   - Dia do mês: 5
   - Data início: 01/01/2025
5. POST /api/recurring-templates/
6. Template criado!
7. Celery criará transação automaticamente todo dia 5
```

### Fluxo 5: Criar Consórcio Parcelado

```mermaid
1. Usuário acessa "Parcelamentos"
2. Clica "Novo Parcelamento"
3. GET /api/categories/?type=expense
4. Preenche:
   - Categoria: "Outros Gastos"
   - Descrição: "Consórcio Carro"
   - Número de parcelas: 30
   - Valor padrão: R$ 500,00
   - Data primeira parcela: 01/11/2025
5. POST /api/installment-plans/
6. Sistema cria 30 parcelas automaticamente!
7. GET /api/installment-plans/{id}/installments/
8. Exibe todas as 30 parcelas
9. Usuário pode editar valor de parcelas específicas
```

### Fluxo 6: Visualizar Parcelas Próximas

```mermaid
1. GET /api/installments/upcoming/?days=30
2. Exibe lista de parcelas dos próximos 30 dias
3. Para cada parcela, mostra:
   - Plano
   - Número da parcela
   - Valor
   - Data de vencimento
   - Status
4. Botão "Marcar como Pago"
5. POST /api/installments/{id}/mark_paid/
```

### Fluxo 7: Relatórios e Gráficos

```mermaid
1. GET /api/transactions/by_month/?year=2025&month=10
2. GET /api/transactions/by_category/?type=expense
3. GET /api/transactions/summary/?start_date=2025-01-01&end_date=2025-12-31
4. Gera gráficos:
   - Pizza: Despesas por categoria
   - Linha: Receitas vs Despesas por mês
   - Barra: Top 5 categorias de gasto
```

---

## ⚙️ Regras de Negócio

### Transações

1. **Categoria deve ser do mesmo tipo**
   - Se transação é `income`, categoria deve ser `income`
   - Se transação é `expense`, categoria deve ser `expense`

2. **Valor deve ser positivo**
   - `amount > 0`

3. **Recorrência**
   - Se `is_recurring = true`, então `recurrence != 'none'`
   - Se `is_recurring = false`, então `recurrence = 'none'`

### Templates Recorrentes

1. **Geração Automática**
   - Só gera se `is_active = true`
   - Só gera se hoje é o `day_of_month` configurado
   - Só gera uma vez por mês (verifica `last_generated_date`)
   - Respeita `start_date` e `end_date`

2. **Dias inválidos**
   - Se configurar dia 31, mas o mês só tem 30 dias, usa último dia do mês

3. **Pausar/Retomar**
   - Pausar: `is_active = false`
   - Retomar: `is_active = true`

### Planos de Parcelamento

1. **Criação Automática de Parcelas**
   - Ao criar plano, cria automaticamente todas as parcelas
   - Parcelas têm vencimento mensal (mes + 1, mes + 2, etc.)

2. **Valores Personalizados**
   - Cada parcela pode ter valor diferente do `default_amount`
   - Editar via `PUT /api/installments/{id}/`

3. **Geração de Transações**
   - Celery cria transação 7 dias antes do `due_date`
   - Só cria se parcela está `pending` ou `overdue`
   - Só cria se não tem `transaction` vinculada
   - Status muda para `generated`

4. **Status Atrasado**
   - Celery atualiza para `overdue` se `due_date < hoje` e status é `pending`

### Paginação

- Todas as listagens são paginadas
- Padrão: 20 itens por página
- Usar `?page=2` para próxima página

### Filtros

- Por data: `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- Por tipo: `?type=income` ou `?type=expense`
- Por categoria: filtrar no frontend após receber dados
- Busca: `?search=texto` (busca em descrição e notas)

---

## 📝 Exemplos de Requisições e Respostas

### Criar Categoria

**Request:**
```http
POST /api/categories/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Academia",
  "type": "expense",
  "description": "Mensalidade e suplementos"
}
```

**Nota:** O campo `user` não precisa ser enviado - é preenchido automaticamente com o usuário logado.

**Response (201):**
```json
{
  "id": 15,
  "name": "Academia",
  "type": "expense",
  "type_display": "Despesa",
  "description": "Mensalidade e suplementos",
  "is_default": false,
  "user": 1,
  "user_email": "usuario@example.com",
  "transactions_count": 0,
  "created_at": "2025-10-08T10:30:00Z",
  "updated_at": "2025-10-08T10:30:00Z"
}
```

**Nota:** O campo `user` retorna automaticamente preenchido com o ID do usuário logado.

### Criar Transação

**Request:**
```http
POST /api/transactions/
Authorization: Bearer {token}
Content-Type: application/json

{
  "category": 15,
  "type": "expense",
  "description": "Academia Smart Fit",
  "amount": "89.90",
  "transaction_date": "2025-10-08",
  "status": "paid",
  "payment_date": "2025-10-08"
}
```

**Response (201):**
```json
{
  "id": 50,
  "user": 1,
  "user_email": "usuario@example.com",
  "category": 15,
  "category_name": "Academia",
  "type": "expense",
  "type_display": "Despesa",
  "description": "Academia Smart Fit",
  "amount": "89.90",
  "transaction_date": "2025-10-08",
  "due_date": null,
  "payment_date": "2025-10-08",
  "is_recurring": false,
  "recurrence": "none",
  "recurrence_display": "Não recorrente",
  "recurrence_end_date": null,
  "status": "paid",
  "status_display": "Pago",
  "notes": null,
  "created_at": "2025-10-08T10:35:00Z",
  "updated_at": "2025-10-08T10:35:00Z"
}
```

### Resumo Financeiro

**Request:**
```http
GET /api/transactions/summary/?start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "total_incomes": 5000.00,
  "total_expenses": 2345.67,
  "balance": 2654.33,
  "total_transactions": 45,
  "pending_transactions": 8,
  "paid_transactions": 35,
  "overdue_transactions": 2
}
```

### Criar Template Recorrente

**Request:**
```http
POST /api/recurring-templates/
Authorization: Bearer {token}
Content-Type: application/json

{
  "category": 1,
  "type": "income",
  "description": "Salário CLT",
  "amount": "5000.00",
  "day_of_month": 5,
  "start_date": "2025-01-01",
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": 1,
  "user": 1,
  "user_email": "usuario@example.com",
  "category": 1,
  "category_name": "Salário",
  "type": "income",
  "type_display": "Receita",
  "description": "Salário CLT",
  "amount": "5000.00",
  "day_of_month": 5,
  "is_active": true,
  "start_date": "2025-01-01",
  "end_date": null,
  "last_generated_date": null,
  "notes": null,
  "created_at": "2025-10-08T10:40:00Z",
  "updated_at": "2025-10-08T10:40:00Z"
}
```

### Criar Plano de Parcelamento

**Request:**
```http
POST /api/installment-plans/
Authorization: Bearer {token}
Content-Type: application/json

{
  "category": 8,
  "type": "expense",
  "description": "Consórcio Honda Civic",
  "total_installments": 30,
  "default_amount": "500.00",
  "start_date": "2025-11-01",
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": 1,
  "user": 1,
  "user_email": "usuario@example.com",
  "category": 8,
  "category_name": "Outros Gastos",
  "type": "expense",
  "type_display": "Despesa",
  "description": "Consórcio Honda Civic",
  "total_installments": 30,
  "default_amount": "500.00",
  "start_date": "2025-11-01",
  "is_active": true,
  "notes": null,
  "installments_count": 30,
  "paid_installments_count": 0,
  "total_amount": "15000.00",
  "created_at": "2025-10-08T10:45:00Z",
  "updated_at": "2025-10-08T10:45:00Z"
}
```

### Listar Parcelas de um Plano

**Request:**
```http
GET /api/installment-plans/1/installments/
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "plan": 1,
    "plan_description": "Consórcio Honda Civic",
    "installment_number": 1,
    "amount": "500.00",
    "due_date": "2025-11-01",
    "status": "pending",
    "status_display": "Pendente",
    "transaction": null,
    "transaction_description": null,
    "notes": null,
    "created_at": "2025-10-08T10:45:00Z",
    "updated_at": "2025-10-08T10:45:00Z"
  },
  {
    "id": 2,
    "plan": 1,
    "plan_description": "Consórcio Honda Civic",
    "installment_number": 2,
    "amount": "500.00",
    "due_date": "2025-12-01",
    "status": "pending",
    "status_display": "Pendente",
    "transaction": null,
    "transaction_description": null,
    "notes": null,
    "created_at": "2025-10-08T10:45:00Z",
    "updated_at": "2025-10-08T10:45:00Z"
  }
  // ... 28 parcelas restantes
]
```

### Resumo de Plano

**Request:**
```http
GET /api/installment-plans/1/summary/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "plan_id": 1,
  "description": "Consórcio Honda Civic",
  "total_installments": 30,
  "pending_installments": 27,
  "paid_installments": 3,
  "overdue_installments": 0,
  "generated_installments": 2,
  "total_amount": 15000.00,
  "paid_amount": 1500.00,
  "pending_amount": 13500.00,
  "progress_percentage": 10.00
}
```

---

## 💻 Requisitos do Frontend

### Tecnologias Sugeridas

- **React** ou **Next.js** (TypeScript)
- **Tailwind CSS** ou **Material-UI**
- **React Query** ou **SWR** (gerenciamento de estado server)
- **Axios** (HTTP client)
- **React Hook Form** + **Zod** (formulários e validação)
- **Recharts** ou **Chart.js** (gráficos)
- **date-fns** ou **dayjs** (manipulação de datas)

### Páginas Principais

#### 1. **Autenticação**
- `/login` - Página de login
- `/register` - Página de registro
- Armazenar tokens em localStorage
- Implementar refresh automático do token

#### 2. **Dashboard** (`/`)
- Resumo financeiro do mês atual
- Saldo total (receitas - despesas)
- Gráfico de receitas vs despesas (últimos 6 meses)
- Últimas 10 transações
- Próximas parcelas a vencer (7 dias)
- Transações pendentes

#### 3. **Transações** (`/transactions`)
- Lista paginada de todas transações
- Filtros:
  - Por período (data início/fim)
  - Por tipo (receita/despesa)
  - Por categoria
  - Por status
- Busca por descrição
- Botões:
  - Nova Transação
  - Editar
  - Deletar
- Indicadores visuais:
  - Verde para receitas
  - Vermelho para despesas
  - Amarelo para pendentes
  - Badge de status

#### 4. **Nova Transação** (`/transactions/new`)
- Formulário:
  - Tipo (toggle receita/despesa)
  - Categoria (select filtrado por tipo)
  - Descrição (input)
  - Valor (input monetário)
  - Data da transação (date picker)
  - Data de vencimento (opcional)
  - Status (select)
  - Observações (textarea)
- Validações:
  - Categoria obrigatória
  - Valor > 0
  - Datas válidas

#### 5. **Categorias** (`/categories`)
- Lista de categorias (padrão + personalizadas)
- Agrupadas por tipo (Receitas / Despesas)
- Número de transações por categoria
- Botões:
  - Nova Categoria
  - Editar (só personalizadas)
  - Deletar (só se não tiver transações)

#### 6. **Transações Recorrentes** (`/recurring`)
- Lista de templates recorrentes
- Cards com:
  - Descrição
  - Valor
  - Dia do mês
  - Status (ativo/pausado)
  - Última geração
  - Próxima geração (calculado)
- Botões:
  - Novo Template
  - Pausar/Retomar
  - Gerar Agora
  - Editar
  - Deletar
- Badge visual:
  - Verde: ativo
  - Cinza: pausado

#### 7. **Novo Template Recorrente** (`/recurring/new`)
- Formulário:
  - Tipo (toggle)
  - Categoria (select)
  - Descrição
  - Valor
  - Dia do mês (1-31)
  - Data de início
  - Data de término (opcional)
  - Ativo (checkbox, padrão true)
  - Observações
- Preview: "Será criada transação todo dia X"

#### 8. **Parcelamentos** (`/installments`)
- Lista de planos de parcelamento
- Cards com:
  - Descrição
  - Progresso (barra de progresso)
  - X de Y parcelas pagas
  - Valor total / Valor pago
  - Próxima parcela
  - Status do plano
- Botões:
  - Novo Parcelamento
  - Ver Detalhes
  - Editar
  - Deletar

#### 9. **Detalhes do Parcelamento** (`/installments/:id`)
- Informações do plano
- Resumo:
  - Total de parcelas
  - Pagas / Pendentes / Atrasadas
  - Valor total / Pago / Restante
  - Progresso (%)
- Lista de todas as parcelas:
  - Número
  - Valor
  - Vencimento
  - Status
  - Transação gerada (link)
  - Botão "Marcar como Pago"
  - Botão "Editar Valor"

#### 10. **Novo Parcelamento** (`/installments/new`)
- Formulário:
  - Tipo (toggle)
  - Categoria (select)
  - Descrição
  - Número de parcelas
  - Valor padrão
  - Data primeira parcela
  - Ativo (checkbox)
  - Observações
- Preview:
  - "Serão criadas X parcelas"
  - "De DD/MM/YYYY a DD/MM/YYYY"
  - "Valor total: R$ X"

#### 11. **Relatórios** (`/reports`)
- Seletor de período
- Gráficos:
  - Pizza: Despesas por categoria
  - Linha: Receitas vs Despesas por mês
  - Barra: Evolução do saldo
  - Barra: Top 5 categorias de gasto
- Tabelas:
  - Resumo por categoria
  - Maiores despesas do período
  - Maiores receitas do período

#### 12. **Perfil** (`/profile`)
- Informações do usuário
- Editar nome
- Trocar senha
- Logout

### Componentes Reutilizáveis

#### `<TransactionCard>`
- Mostra uma transação
- Props: transaction, onEdit, onDelete

#### `<CategoryBadge>`
- Badge colorido com nome da categoria
- Props: category

#### `<StatusBadge>`
- Badge de status (pending, paid, overdue)
- Props: status

#### `<MoneyDisplay>`
- Formata valor em real
- Cor verde para positivo, vermelho para negativo
- Props: amount, type

#### `<DatePicker>`
- Seletor de data customizado
- Props: value, onChange, label

#### `<ProgressBar>`
- Barra de progresso para parcelas
- Props: current, total, percentage

#### `<ConfirmModal>`
- Modal de confirmação para ações destrutivas
- Props: title, message, onConfirm, onCancel

### Estados e Contextos

#### `AuthContext`
```typescript
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

#### `FinanceContext` (opcional)
```typescript
interface FinanceContextType {
  categories: Category[];
  refreshCategories: () => void;
}
```

### Formatações

#### Dinheiro
```typescript
// R$ 1.500,00
function formatMoney(value: string | number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(Number(value));
}
```

#### Data
```typescript
// 08/10/2025
function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('pt-BR');
}
```

#### Data para API
```typescript
// YYYY-MM-DD
function toAPIDate(date: Date): string {
  return date.toISOString().split('T')[0];
}
```

### Validações

#### Formulário de Transação
```typescript
const transactionSchema = z.object({
  category: z.number().min(1, "Categoria obrigatória"),
  type: z.enum(['income', 'expense']),
  description: z.string().min(3, "Mínimo 3 caracteres"),
  amount: z.string().refine(val => parseFloat(val) > 0, "Valor deve ser maior que zero"),
  transaction_date: z.string(),
  status: z.enum(['pending', 'paid', 'overdue']),
});
```

### Mensagens de Erro

- **400 Bad Request**: "Dados inválidos. Verifique os campos."
- **401 Unauthorized**: "Sessão expirada. Faça login novamente."
- **403 Forbidden**: "Você não tem permissão para esta ação."
- **404 Not Found**: "Recurso não encontrado."
- **500 Server Error**: "Erro no servidor. Tente novamente mais tarde."

### Mensagens de Sucesso

- Transação criada: "Transação criada com sucesso!"
- Transação atualizada: "Transação atualizada!"
- Transação deletada: "Transação removida!"
- Template criado: "Template recorrente criado! Transações serão geradas automaticamente."
- Plano criado: "Plano de parcelamento criado! X parcelas geradas."
- Parcela paga: "Parcela marcada como paga!"

---

## 🎨 Design System Sugerido

### Cores

**Principais:**
- Primary: `#10b981` (Verde - Receitas)
- Danger: `#ef4444` (Vermelho - Despesas)
- Warning: `#f59e0b` (Amarelo - Pendentes)
- Info: `#3b82f6` (Azul - Informações)
- Success: `#22c55e` (Verde claro - Sucesso)

**Neutras:**
- Background: `#f9fafb`
- Card: `#ffffff`
- Border: `#e5e7eb`
- Text Primary: `#111827`
- Text Secondary: `#6b7280`

### Tipografia

- **Fonte**: Inter, Roboto ou System UI
- **Títulos**: 24px - 32px (font-bold)
- **Subtítulos**: 18px - 20px (font-semibold)
- **Corpo**: 14px - 16px (font-normal)
- **Small**: 12px - 14px (font-normal)

### Espaçamento

- **XS**: 4px
- **SM**: 8px
- **MD**: 16px
- **LG**: 24px
- **XL**: 32px

### Breakpoints (Responsividade)

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

---

## 📱 Funcionalidades Extras (Opcionais)

### Nível 1 (MVP)
✅ Autenticação  
✅ Transações CRUD  
✅ Categorias  
✅ Dashboard básico  
✅ Filtros por período  

### Nível 2 (Essencial)
✅ Templates recorrentes  
✅ Parcelamentos  
✅ Relatórios  
✅ Gráficos  

### Nível 3 (Avançado)
- 🔔 Notificações (parcelas próximas ao vencimento)
- 📊 Metas financeiras
- 💾 Exportar relatórios (PDF/Excel)
- 🌙 Dark mode
- 📱 PWA (Progressive Web App)
- 🔄 Sincronização offline

---

## 🚀 Como Começar

### 1. Setup Inicial

```bash
npx create-next-app@latest mydindin-frontend
cd mydindin-frontend
npm install axios react-query @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Configurar API Client

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### 3. Criar Tipos

```typescript
// types/index.ts
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
}

export interface Category {
  id: number;
  name: string;
  type: 'income' | 'expense';
  type_display: string;
  description?: string;
  // ... outros campos
}

// ... demais interfaces
```

### 4. Primeiro Endpoint

```typescript
// hooks/useTransactions.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export function useTransactions() {
  return useQuery({
    queryKey: ['transactions'],
    queryFn: async () => {
      const { data } = await api.get('/transactions/');
      return data;
    },
  });
}
```

---

## 📚 Documentação Adicional

Para mais informações:
- **MOTOR_RECORRENCIA.md** - Documentação completa do sistema de recorrência
- **API_EXAMPLES.md** - Mais exemplos de requisições
- **QUICK_START_CELERY.md** - Como rodar o backend

---

## ✅ Checklist de Implementação

### Autenticação
- [ ] Tela de login
- [ ] Tela de registro
- [ ] Armazenamento de tokens
- [ ] Refresh automático
- [ ] Logout
- [ ] Rotas protegidas

### Dashboard
- [ ] Resumo financeiro
- [ ] Últimas transações
- [ ] Gráficos básicos
- [ ] Próximas parcelas

### Transações
- [ ] Listar transações
- [ ] Criar transação
- [ ] Editar transação
- [ ] Deletar transação
- [ ] Filtros (período, tipo, categoria)
- [ ] Paginação

### Categorias
- [ ] Listar categorias
- [ ] Criar categoria
- [ ] Editar categoria
- [ ] Deletar categoria

### Templates Recorrentes
- [ ] Listar templates
- [ ] Criar template
- [ ] Editar template
- [ ] Pausar/Retomar
- [ ] Gerar transação manualmente
- [ ] Deletar template

### Parcelamentos
- [ ] Listar planos
- [ ] Criar plano
- [ ] Ver detalhes (com parcelas)
- [ ] Editar plano
- [ ] Deletar plano
- [ ] Editar parcela individual
- [ ] Marcar parcela como paga
- [ ] Ver parcelas próximas

### Relatórios
- [ ] Gráfico de receitas vs despesas
- [ ] Gráfico por categoria
- [ ] Resumo por período
- [ ] Exportar (opcional)

---

**Boa sorte no desenvolvimento do frontend! 🚀**

Este contexto deve ser suficiente para uma IA criar uma aplicação frontend completa e funcional.

