# 🚀 Quick Start - Motor de Recorrência

Guia rápido para iniciar o sistema de recorrência e parcelamento do MyDinDin.

## ⚡ Instalação Rápida

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
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results
```

### 3. Criar Superusuário (se ainda não tiver)

```bash
python manage.py createsuperuser
```

### 4. Carregar Categorias Padrão

```bash
python manage.py load_default_categories
```

---

## 🔴 Iniciar Redis

**Opção 1: Redis via Docker**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**Opção 2: Redis instalado localmente**
```bash
# Instalar (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install redis-server

# Iniciar
redis-server
```

**Verificar se Redis está funcionando:**
```bash
redis-cli ping
# Deve retornar: PONG
```

---

## 🏃 Iniciar o Sistema

Você precisa de **4 terminais** rodando simultaneamente:

### Terminal 1: Django Server

```bash
cd /home/vi/dev/mydindin
eval "$(pyenv init -)" && pyenv shell mydindin
python manage.py runserver
```

Acesse: `http://localhost:8000/admin/`

---

### Terminal 2: Celery Worker

```bash
cd /home/vi/dev/mydindin
eval "$(pyenv init -)" && pyenv shell mydindin
celery -A config worker --loglevel=info
```

**O que faz:** Processa tarefas assíncronas

---

### Terminal 3: Celery Beat

```bash
cd /home/vi/dev/mydindin
eval "$(pyenv init -)" && pyenv shell mydindin
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**O que faz:** Agenda tarefas periódicas (00:01, 00:05, 00:10 diariamente)

---

### Terminal 4: Redis (se não estiver rodando)

```bash
redis-server
```

---

## ✅ Verificar se Está Funcionando

### 1. Verificar Celery Worker

```bash
celery -A config inspect active
```

Deve retornar status dos workers.

### 2. Verificar Tarefas Agendadas

```bash
celery -A config inspect scheduled
```

### 3. Acessar Django Admin

1. Acesse `http://localhost:8000/admin/`
2. Login com superusuário
3. Você deve ver:
   - Categories
   - Transactions
   - **Recurring Templates** ✨
   - **Installment Plans** ✨
   - **Installments** ✨
   - Periodic Tasks (Celery Beat)

---

## 🧪 Testar o Sistema

### Teste 1: Template Recorrente (API)

```bash
# Login e pegar token
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"suasenha"}'

# Criar template (substitua {TOKEN})
curl -X POST http://localhost:8000/api/recurring-templates/ \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "category": 1,
    "type": "income",
    "description": "Salário Teste",
    "amount": "5000.00",
    "day_of_month": 15,
    "start_date": "2025-01-01",
    "is_active": true
  }'
```

### Teste 2: Plano de Parcelamento (Django Admin)

1. Acesse `/admin/finances/installmentplan/`
2. Clique em "Add Installment Plan"
3. Preencha:
   - Description: "Consórcio Teste"
   - Type: Expense
   - Category: (escolha uma)
   - Total installments: 10
   - Default amount: 500.00
   - Start date: data futura
4. Salvar

**Resultado:** 10 parcelas criadas automaticamente!

### Teste 3: Gerar Transação Manualmente

```bash
# Pegar ID do template criado
curl http://localhost:8000/api/recurring-templates/ \
  -H "Authorization: Bearer {TOKEN}"

# Gerar transação agora (sem esperar Celery)
curl -X POST http://localhost:8000/api/recurring-templates/1/generate_now/ \
  -H "Authorization: Bearer {TOKEN}"
```

---

## 📅 Horários Automáticos

O Celery executará automaticamente:

| Horário | Ação |
|---------|------|
| 00:01 | Cria transações de templates recorrentes |
| 00:05 | Cria transações de parcelas próximas ao vencimento |
| 00:10 | Atualiza status de transações/parcelas atrasadas |
| 03:00 (dia 1) | Limpeza mensal (opcional) |

---

## 🐛 Troubleshooting Rápido

### Redis não conecta
```bash
# Verificar se está rodando
redis-cli ping

# Se não estiver, iniciar
redis-server
```

### Celery não está ativo
```bash
# Verificar processos
ps aux | grep celery

# Matar todos
pkill -f celery

# Reiniciar worker e beat
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Migrations faltando
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results
```

### Erro de módulo não encontrado
```bash
# Reinstalar dependências
pip install -r requirements.txt --upgrade
```

---

## 📖 Documentação Completa

Para documentação detalhada, veja:
- **MOTOR_RECORRENCIA.md** - Guia completo com exemplos
- **API_EXAMPLES.md** - Exemplos de requisições
- **SETUP.md** - Setup geral do projeto

---

## 🎯 Resumo dos Comandos

```bash
# Iniciar tudo (4 terminais)

# T1: Django
python manage.py runserver

# T2: Celery Worker
celery -A config worker --loglevel=info

# T3: Celery Beat  
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# T4: Redis
redis-server
```

**Pronto! Sistema rodando! 🚀**

