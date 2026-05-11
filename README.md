# MyDinDin - Sistema de Controle Financeiro

Sistema de controle de finanças pessoais desenvolvido com Django REST Framework.

## Funcionalidades

- **Categorias**: Gerenciamento de categorias de receitas e despesas (com categorias padrão)
- **Transações**: Registro de receitas e despesas
- **Recorrência**: Suporte para transações mensais recorrentes
- **Data Máxima**: Controle de pagamento até data limite (útil para condomínio, etc)
- **API REST**: Interface completa para integração
- **Autenticação JWT**: Bearer token com renovação automática de 10 dias

## Tecnologias

- Python 3.12
- Django 5.1.2
- Django REST Framework 3.15.2
- Simple JWT para autenticação (Bearer Token)
- PostgreSQL (banco de dados)
- Custom User Model (autenticação por email)

## Instalação

1. Ative o ambiente virtual:
```bash
pyenv activate mydindin
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
# Crie um arquivo .env na raiz do projeto com as seguintes variáveis:
SECRET_KEY=your-secret-key-here
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
```

4. Crie o banco de dados PostgreSQL:
```bash
# No PostgreSQL, execute:
CREATE DATABASE mydindin;
```

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
# Será solicitado: email, first_name, last_name e password
# Nota: O login é feito usando EMAIL ao invés de username
```

7. Carregue as categorias padrão:
```bash
python manage.py load_default_categories
```

8. Execute o servidor:
```bash
python manage.py runserver
```

## Endpoints da API

### Autenticação
- `POST /api/auth/register/` - Registrar novo usuário
  - Body: `{"email": "user@example.com", "first_name": "Nome", "last_name": "Sobrenome", "password": "senha123", "password_confirm": "senha123"}`
- `POST /api/auth/login/` - Login (retorna access e refresh token com validade de 10 dias)
  - Body: `{"email": "user@example.com", "password": "senha123"}`
- `POST /api/auth/token/refresh/` - Renovar token
  - Body: `{"refresh": "refresh_token_aqui"}`
- `POST /api/auth/logout/` - Logout (blacklist do refresh token)
  - Body: `{"refresh": "refresh_token_aqui"}`
- `GET /api/auth/profile/` - Obter perfil do usuário logado
  - Header: `Authorization: Bearer access_token_aqui`

### Categorias
- `GET /api/categories/` - Listar categorias (padrão e do usuário)
- `POST /api/categories/` - Criar categoria
- `GET /api/categories/{id}/` - Detalhes da categoria
- `PUT /api/categories/{id}/` - Atualizar categoria
- `DELETE /api/categories/{id}/` - Deletar categoria
- `GET /api/categories/by_type/?type=income` - Listar categorias por tipo (income/expense)

### Transações
- `GET /api/transactions/` - Listar transações
- `POST /api/transactions/` - Criar transação
- `GET /api/transactions/{id}/` - Detalhes da transação
- `PUT /api/transactions/{id}/` - Atualizar transação
- `DELETE /api/transactions/{id}/` - Deletar transação
- `GET /api/transactions/by_period/?start_date=2024-01-01&end_date=2024-12-31` - Filtrar por período
- `GET /api/transactions/by_month/?year=2024&month=10` - Filtrar por mês
- `GET /api/transactions/summary/` - Resumo financeiro (total receitas, despesas, saldo)
- `GET /api/transactions/by_category/?type=expense` - Agrupar por categoria

**Nota**: Todos os endpoints de categorias e transações requerem autenticação via Bearer Token.

## Admin

Acesse o painel administrativo em: `http://localhost:8000/admin/`

**Login**: Use seu **email** e senha (não username).

## Categorias Padrão

O sistema vem com categorias padrão pré-configuradas:

**Receitas:**
- Salário
- Freelance
- Investimentos
- Outras Receitas

**Despesas:**
- Moradia (aluguel, condomínio, IPTU)
- Alimentação
- Transporte
- Saúde
- Educação
- Lazer
- Contas e Serviços (água, luz, internet)
- Vestuário
- Outras Despesas

Você pode criar suas próprias categorias personalizadas através da API ou Admin.

