#!/bin/bash

echo "🚀 Inicializando projeto MyDinDin..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se está no ambiente virtual correto
if [[ "$VIRTUAL_ENV" != *"mydindin"* ]]; then
    echo -e "${YELLOW}⚠️  Ativando ambiente virtual mydindin...${NC}"
    eval "$(pyenv init -)"
    pyenv activate mydindin
fi

# Verificar se .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Criando...${NC}"
    cat > .env << EOF
SECRET_KEY=django-insecure-change-this-in-production-$(date +%s)
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
    echo -e "${GREEN}✅ Arquivo .env criado!${NC}"
else
    echo -e "${GREEN}✅ Arquivo .env encontrado${NC}"
fi

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Dependências instaladas${NC}"

# Criar migrations
echo ""
echo "🔨 Criando migrations..."
python manage.py makemigrations
echo -e "${GREEN}✅ Migrations criadas${NC}"

# Executar migrations
echo ""
echo "⚙️  Executando migrations..."
python manage.py migrate
echo -e "${GREEN}✅ Banco de dados configurado${NC}"

# Carregar categorias padrão
echo ""
echo "📁 Carregando categorias padrão..."
python manage.py load_default_categories
echo -e "${GREEN}✅ Categorias padrão carregadas${NC}"

# Perguntar se quer criar superusuário
echo ""
read -p "Deseja criar um superusuário agora? (s/n): " criar_super

if [ "$criar_super" = "s" ] || [ "$criar_super" = "S" ]; then
    echo ""
    echo "👤 Criando superusuário..."
    echo -e "${YELLOW}Lembre-se: Use EMAIL para login (não username)${NC}"
    python manage.py createsuperuser
fi

# Mensagem final
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Projeto MyDinDin configurado com sucesso!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Para iniciar o servidor, execute:"
echo -e "${YELLOW}python manage.py runserver${NC}"
echo ""
echo "Acesse:"
echo "  - Admin: http://localhost:8000/admin/"
echo "  - API: http://localhost:8000/api/"
echo ""
echo "📚 Documentação:"
echo "  - README.md - Visão geral"
echo "  - SETUP.md - Instruções detalhadas"
echo "  - API_EXAMPLES.md - Exemplos de uso"
echo "  - PROJETO_COMPLETO.md - Resumo completo"
echo ""
echo -e "${GREEN}Bom desenvolvimento! 🚀${NC}"
echo ""

