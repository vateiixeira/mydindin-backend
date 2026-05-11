# 🔄 Motor de Recorrência e Parcelamento - MyDinDin

Este documento descreve o sistema de criação automática de transações recorrentes e parceladas implementado no MyDinDin.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Templates Recorrentes](#templates-recorrentes)
4. [Planos de Parcelamento](#planos-de-parcelamento)
5. [Celery - Automação](#celery---automação)
6. [APIs REST](#apis-rest)
7. [Exemplos de Uso](#exemplos-de-uso)

---

## 🎯 Visão Geral

O sistema implementa três novos modelos para gerenciar transações automáticas:

### **RecurringTemplate** - Templates Recorrentes
- Cria transações automaticamente em dias específicos do mês
- Ideal para: salários, aluguéis, assinaturas, contas fixas
- Exemplo: Salário de R$ 5.000 todo dia 5

### **InstallmentPlan** - Planos de Parcelamento  
- Gerencia compras/vendas parceladas
- Cria todas as parcelas automaticamente
- Exemplo: Consórcio de 30 parcelas de R$ 500

### **Installment** - Parcelas Individuais
- Cada parcela pode ter valor e vencimento personalizados
- Gera transações automaticamente próximo ao vencimento
- Rastreamento de status individual

---

## 🔧 Instalação

### 1. Instalar Dependências

```bash
cd /home/vi/dev/mydindin
eval "$(pyenv init -)"
pyenv shell mydindin
pip install -r requirements.txt
```

### 2. Aplicar Migrations

```bash
python manage.py migrate
```

### 3. Iniciar Redis (Necessário para o Celery)

```bash
# Instalar Redis (se não tiver)
sudo apt-get install redis-server

# Iniciar Redis
redis-server
```

### 4. Iniciar Celery Worker e Beat

**Terminal 1 - Worker:**
```bash
cd /home/vi/dev/mydindin
eval "$(pyenv init -)" && pyenv shell mydindin
celery -A config worker --loglevel=info
```

**Terminal 2 - Beat (Scheduler):**
```bash
cd /home/vi/dev/mydindin
eval "$(pyenv init -)" && pyenv shell mydindin
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 💰 Templates Recorrentes

### Modelo: RecurringTemplate

Cria transações automaticamente em dias específicos do mês.

**Campos:**
- `description`: Descrição (ex: "Salário")
- `type`: `income` ou `expense`
- `category`: Categoria da transação
- `amount`: Valor fixo
- `day_of_month`: Dia do mês (1-31)
- `is_active`: Ativo/Pausado
- `start_date`: Data de início
- `end_date`: Data de término (opcional)
- `last_generated_date`: Última geração (automático)

### Quando é Gerado?

O Celery executa **diariamente às 00:01** e verifica:
1. Se o template está ativo
2. Se hoje é o dia configurado
3. Se ainda não gerou este mês
4. Se não passou da data de término

### Exemplo de Uso

**Criar um salário recorrente:**
```json
POST /api/recurring-templates/
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

Resultado: Todo dia 5, uma transação de R$ 5.000 será criada automaticamente!

---

## 📦 Planos de Parcelamento

### Modelo: InstallmentPlan

Gerencia compras ou vendas parceladas.

**Campos:**
- `description`: Descrição (ex: "Consórcio Carro")
- `type`: `income` ou `expense`
- `category`: Categoria
- `total_installments`: Número de parcelas
- `default_amount`: Valor padrão das parcelas
- `start_date`: Data da primeira parcela
- `is_active`: Ativo/Pausado

### Comportamento

Ao criar um plano:
1. **Cria automaticamente todas as parcelas** (Installments)
2. Cada parcela tem vencimento mensal
3. Você pode editar valores individuais de cada parcela

### Modelo: Installment

Cada parcela individual do plano.

**Campos:**
- `plan`: Plano pai
- `installment_number`: Número da parcela (1, 2, 3...)
- `amount`: Valor (pode ser diferente do padrão)
- `due_date`: Data de vencimento
- `status`: `pending`, `generated`, `paid`, `overdue`
- `transaction`: Transação gerada (automático)

### Quando é Gerado?

O Celery executa **diariamente às 00:05** e:
1. Busca parcelas com vencimento próximo (7 dias antes)
2. Cria uma Transaction para cada parcela
3. Vincula a parcela à transação
4. Atualiza status para `generated`

### Exemplo de Uso

**Criar um consórcio de 30 parcelas:**
```json
POST /api/installment-plans/
{
  "category": 2,
  "type": "expense",
  "description": "Consórcio Carro",
  "total_installments": 30,
  "default_amount": "500.00",
  "start_date": "2025-11-01",
  "is_active": true
}
```

Resultado:
- 30 parcelas criadas automaticamente
- Vencimentos mensais (01/11/2025, 01/12/2025, ...)
- Transações criadas 7 dias antes de cada vencimento

**Editar valor de uma parcela específica:**
```json
PUT /api/installments/5/
{
  "amount": "550.00"
}
```

---

## ⚙️ Celery - Automação

O Celery executa tarefas automatizadas em horários programados:

### Tasks Agendadas

| Task | Horário | Função |
|------|---------|--------|
| `create_recurring_transactions` | 00:01 diária | Cria transações de templates recorrentes |
| `create_installment_transactions` | 00:05 diária | Cria transações de parcelas |
| `update_overdue_status` | 00:10 diária | Atualiza status de atrasados |
| `cleanup_old_data` | 03:00 dia 1 | Limpeza mensal (opcional) |

### Verificar Status

```bash
# Ver logs do worker
celery -A config inspect active

# Ver tasks agendadas
celery -A config inspect scheduled
```

### Executar Manualmente

Você pode gerar transações manualmente via API sem esperar o Celery:

```bash
POST /api/recurring-templates/{id}/generate_now/
POST /api/installments/{id}/mark_paid/
```

---

## 🌐 APIs REST

### RecurringTemplate

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/recurring-templates/` | Listar templates |
| POST | `/api/recurring-templates/` | Criar template |
| GET | `/api/recurring-templates/{id}/` | Detalhe |
| PUT | `/api/recurring-templates/{id}/` | Atualizar |
| DELETE | `/api/recurring-templates/{id}/` | Deletar |
| POST | `/api/recurring-templates/{id}/pause/` | Pausar |
| POST | `/api/recurring-templates/{id}/resume/` | Retomar |
| POST | `/api/recurring-templates/{id}/generate_now/` | Gerar agora |
| GET | `/api/recurring-templates/active/` | Só ativos |

### InstallmentPlan

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/installment-plans/` | Listar planos |
| POST | `/api/installment-plans/` | Criar plano |
| GET | `/api/installment-plans/{id}/` | Detalhe com parcelas |
| PUT | `/api/installment-plans/{id}/` | Atualizar |
| DELETE | `/api/installment-plans/{id}/` | Deletar |
| GET | `/api/installment-plans/{id}/installments/` | Listar parcelas |
| GET | `/api/installment-plans/{id}/pending_installments/` | Parcelas pendentes |
| GET | `/api/installment-plans/{id}/summary/` | Resumo do plano |

### Installment

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/installments/` | Listar parcelas |
| GET | `/api/installments/{id}/` | Detalhe |
| PUT | `/api/installments/{id}/` | Atualizar |
| GET | `/api/installments/upcoming/` | Próximas a vencer |
| GET | `/api/installments/overdue/` | Atrasadas |
| POST | `/api/installments/{id}/mark_paid/` | Marcar como pago |

---

## 💡 Exemplos de Uso

### Caso 1: Salário Mensal

```bash
# Criar template
POST /api/recurring-templates/
{
  "category": 1,
  "type": "income",
  "description": "Salário",
  "amount": "5000.00",
  "day_of_month": 5,
  "start_date": "2025-01-01",
  "is_active": true
}

# Resultado: Todo dia 5, transação de R$ 5.000 criada automaticamente!
```

### Caso 2: Aluguel

```bash
POST /api/recurring-templates/
{
  "category": 3,
  "type": "expense",
  "description": "Aluguel",
  "amount": "1500.00",
  "day_of_month": 10,
  "start_date": "2025-01-01",
  "is_active": true
}
```

### Caso 3: Consórcio com Valores Variáveis

```bash
# 1. Criar plano
POST /api/installment-plans/
{
  "category": 2,
  "type": "expense",
  "description": "Consórcio Imóvel",
  "total_installments": 30,
  "default_amount": "800.00",
  "start_date": "2025-11-01"
}

# Resposta: { "id": 5, ... }

# 2. Ajustar parcela específica (ex: parcela 5 tem taxa extra)
GET /api/installment-plans/5/installments/
# Pegar ID da parcela 5

PUT /api/installments/25/
{
  "amount": "850.00",
  "notes": "Parcela com taxa de administração"
}
```

### Caso 4: Financiamento de Carro

```bash
POST /api/installment-plans/
{
  "category": 4,
  "type": "expense", 
  "description": "Financiamento Honda Civic",
  "total_installments": 48,
  "default_amount": "1200.00",
  "start_date": "2025-12-15"
}

# Ver resumo
GET /api/installment-plans/6/summary/

# Resposta:
{
  "total_installments": 48,
  "pending_installments": 45,
  "paid_installments": 3,
  "total_amount": 57600.00,
  "paid_amount": 3600.00,
  "pending_amount": 54000.00,
  "progress_percentage": 6.25
}
```

### Caso 5: Pausar Template Temporariamente

```bash
# Pausar salário (ex: férias)
POST /api/recurring-templates/1/pause/

# Retomar depois
POST /api/recurring-templates/1/resume/
```

---

## 📊 Admin Django

Todos os modelos estão disponíveis no Django Admin (`/admin/`):

- **Categories**: Gerenciar categorias
- **Transactions**: Ver todas transações
- **Recurring Templates**: Gerenciar templates recorrentes
- **Installment Plans**: Gerenciar planos com parcelas inline
- **Installments**: Gerenciar parcelas individuais

### Actions em Massa

- Templates: Ativar/Desativar em massa
- Planos: Ativar/Desativar em massa  
- Parcelas: Marcar como pago/pendente em massa

---

## 🔍 Troubleshooting

### Celery não está criando transações

1. Verificar se Redis está rodando:
```bash
redis-cli ping
# Deve retornar: PONG
```

2. Verificar se Worker está ativo:
```bash
celery -A config inspect active
```

3. Verificar se Beat está agendado:
```bash
celery -A config inspect scheduled
```

4. Ver logs:
```bash
# No terminal do worker/beat
```

### Transação não foi gerada

1. Verificar se template está ativo:
```bash
GET /api/recurring-templates/
# Verificar campo "is_active": true
```

2. Verificar `last_generated_date`:
- Se já gerou este mês, não gera novamente

3. Gerar manualmente:
```bash
POST /api/recurring-templates/{id}/generate_now/
```

### Parcela não criou transação

1. Verificar status da parcela:
- Deve estar `pending` ou `overdue`
- Não pode já ter `transaction`

2. Verificar vencimento:
- Transação é criada 7 dias antes

3. Verificar se plano está ativo:
```bash
GET /api/installment-plans/{id}/
# "is_active": true
```

---

## 📚 Arquitetura

```
finances/
├── models.py                      # Modelos RecurringTemplate, InstallmentPlan, Installment
├── serializers.py                 # Serializers REST
├── views.py                       # ViewSets com actions customizadas
├── tasks.py                       # Tasks do Celery
├── admin.py                       # Django Admin
├── urls.py                        # Rotas da API
└── services/
    ├── recurring_service.py       # Lógica de templates recorrentes
    └── installment_service.py     # Lógica de parcelamento

config/
├── celery.py                      # Configuração Celery + Beat Schedule
└── settings.py                    # Settings Django + Celery
```

---

## 🎓 Próximos Passos

1. **Instalar e configurar** Redis + Celery
2. **Criar categorias** no Django Admin
3. **Testar** criando um template recorrente
4. **Testar** criando um plano de parcelamento
5. **Monitorar** logs do Celery

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar este documento
2. Ver logs do Celery
3. Verificar Django Admin
4. Testar APIs manualmente

**Bom uso do sistema de recorrência! 🚀**

