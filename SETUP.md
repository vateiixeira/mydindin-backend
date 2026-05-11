# Guia de Configuração do MyDinDin

## Pré-requisitos

- Python 3.12
- PostgreSQL instalado e rodando
- pyenv com ambiente virtual `mydindin` criado

## Passo a Passo

### 1. Ativar ambiente virtual

```bash
pyenv activate mydindin
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL

#### 3.1. Criar banco de dados

Entre no PostgreSQL:
```bash
sudo -u postgres psql
```

Execute os comandos SQL:
```sql
CREATE DATABASE mydindin;
CREATE USER mydindin_user WITH PASSWORD 'sua_senha_aqui';
ALTER ROLE mydindin_user SET client_encoding TO 'utf8';
ALTER ROLE mydindin_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE mydindin_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE mydindin TO mydindin_user;
\q
```

**Nota**: Para desenvolvimento local, você pode usar o usuário `postgres` padrão.

### 4. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
cat > .env << EOF
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mydindin
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOW_ALL_ORIGINS=True
EOF
```

**IMPORTANTE**: Altere a `SECRET_KEY` em produção!

### 5. Executar migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Criar superusuário

```bash
python manage.py createsuperuser
```

Será solicitado:
- **Email**: seu@email.com
- **First name**: Seu Nome
- **Last name**: Seu Sobrenome
- **Password**: sua senha

**IMPORTANTE**: O login é feito com EMAIL, não username!

### 7. Carregar categorias padrão

```bash
python manage.py load_default_categories
```

### 8. Executar servidor

```bash
python manage.py runserver
```

Acesse:
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## Testando a API

### Registrar novo usuário

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "first_name": "Teste",
    "last_name": "Usuario",
    "password": "senha123",
    "password_confirm": "senha123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "password": "senha123"
  }'
```

Você receberá:
```json
{
  "user": {...},
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

### Listar categorias (com autenticação)

```bash
curl -X GET http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

### Criar uma transação

```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "category": 1,
    "type": "expense",
    "description": "Compra no supermercado",
    "amount": "150.50",
    "transaction_date": "2024-10-08",
    "status": "paid"
  }'
```

## Troubleshooting

### Erro de conexão com PostgreSQL

Verifique se o PostgreSQL está rodando:
```bash
sudo systemctl status postgresql
```

Inicie se necessário:
```bash
sudo systemctl start postgresql
```

### Erro de permissão no banco

Certifique-se que o usuário tem permissões:
```sql
GRANT ALL PRIVILEGES ON DATABASE mydindin TO seu_usuario;
```

### Token expirado

O access token tem validade de 10 dias. Se expirar, use o refresh token:
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "SEU_REFRESH_TOKEN"
  }'
```

