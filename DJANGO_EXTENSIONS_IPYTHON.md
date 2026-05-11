# 🐍 Django Extensions + IPython

## 📦 O que foi Instalado

- ✅ **django-extensions** 4.1 - Extensões úteis para Django
- ✅ **ipython** 9.6.0 - Shell interativo avançado do Python
- ✅ Configurado no `settings.py` para usar automaticamente

## 🚀 Comandos Disponíveis

### 1. Shell Plus (Melhor que o shell padrão!)

O `shell_plus` carrega automaticamente todos os seus modelos:

```bash
python manage.py shell_plus
```

**Vantagens**:
- ✅ Todos os modelos importados automaticamente
- ✅ Interface IPython com autocomplete avançado
- ✅ Sintaxe colorida
- ✅ Histórico de comandos persistente
- ✅ Magic commands do IPython

#### Exemplo de uso:

```python
# Inicia o shell
$ python manage.py shell_plus

# Seus modelos já estão importados!
>>> User.objects.all()
<QuerySet [<User: vi@exemplo.com>]>

>>> Transaction.objects.filter(type='income').count()
42

>>> Category.objects.create(
...     name='Nova Categoria',
...     type='expense',
...     user=User.objects.first()
... )
```

### 2. Shell Plus com SQL Debugging

Para ver todas as queries SQL executadas:

```bash
python manage.py shell_plus --print-sql
```

Ou configure permanentemente no `settings.py`:
```python
SHELL_PLUS_PRINT_SQL = True  # Já está configurado como False
```

### 3. Outros Comandos Úteis do Django Extensions

#### show_urls - Ver todas as URLs do projeto
```bash
python manage.py show_urls
```

Mostra todas as rotas da API:
```
/api/categories/                           finances.views.CategoryViewSet
/api/transactions/                         finances.views.TransactionViewSet
/api/transactions/by_period/              finances.views.TransactionViewSet
...
```

#### show_urls com filtro
```bash
python manage.py show_urls | grep api
python manage.py show_urls | grep transactions
```

#### graph_models - Gerar diagrama de modelos
```bash
# Instale o pygraphviz primeiro:
# sudo apt install graphviz libgraphviz-dev
# pip install pygraphviz

python manage.py graph_models -a -g -o models.png
```

#### validate_templates - Validar templates
```bash
python manage.py validate_templates
```

#### clean_pyc - Limpar arquivos .pyc
```bash
python manage.py clean_pyc
```

#### reset_db - Resetar banco de dados (cuidado!)
```bash
python manage.py reset_db
```

#### sqldiff - Ver diferenças entre modelos e banco
```bash
python manage.py sqldiff -a
```

## 🎯 IPython Features

### Magic Commands

```python
# Ver histórico
%history

# Executar script externo
%run script.py

# Medir tempo de execução
%timeit User.objects.count()

# Ver documentação
?User.objects.create

# Ver código fonte
??User.objects.create

# Listar variáveis
%who
%whos

# Salvar histórico em arquivo
%save historico.py 1-10

# Limpar tela
%clear
```

### Autocompletar Avançado

Basta apertar `TAB`:

```python
>>> User.objects.f<TAB>
User.objects.filter(
User.objects.first(

>>> transaction.<TAB>
transaction.amount
transaction.category
transaction.description
...
```

### Histórico Persistente

Use `↑` e `↓` para navegar pelo histórico de comandos entre sessões.

### Busca no Histórico

```python
# Buscar comandos anteriores
# Ctrl + R e digite parte do comando
```

## 📝 Exemplos Práticos

### 1. Analisar Dados Financeiros

```python
$ python manage.py shell_plus

# Ver total de receitas
>>> from django.db.models import Sum
>>> Transaction.objects.filter(type='income').aggregate(Sum('amount'))
{'amount__sum': Decimal('15000.00')}

# Ver despesas por categoria
>>> from collections import defaultdict
>>> despesas = defaultdict(float)
>>> for t in Transaction.objects.filter(type='expense'):
...     despesas[t.category.name] += float(t.amount)
>>> 
>>> for cat, total in sorted(despesas.items()):
...     print(f"{cat}: R$ {total:.2f}")
```

### 2. Testar Funcionalidades

```python
# Testar sincronização de parcelas
>>> installment = Installment.objects.first()
>>> print(f"Parcela: R$ {installment.amount}")
>>> print(f"Transação: R$ {installment.transaction.amount}")

# Atualizar e verificar
>>> installment.amount = Decimal('500.00')
>>> installment.save()
# Nota: A sincronização automática só funciona via API!
```

### 3. Criar Dados de Teste

```python
# Criar usuário
>>> user = User.objects.create_user(
...     email='teste@example.com',
...     name='Teste',
...     password='senha123'
... )

# Criar categoria
>>> cat = Category.objects.create(
...     name='Alimentação',
...     type='expense',
...     user=user
... )

# Criar transação
>>> trans = Transaction.objects.create(
...     user=user,
...     category=cat,
...     type='expense',
...     description='Supermercado',
...     amount=Decimal('150.00'),
...     transaction_date=date.today()
... )
```

### 4. Debug de Problemas

```python
# Ver queries executadas
>>> from django.db import connection
>>> connection.queries

# Limpar queries log
>>> connection.queries.clear()

# Verificar configurações
>>> from django.conf import settings
>>> settings.DEBUG
>>> settings.DATABASES

# Verificar apps instalados
>>> settings.INSTALLED_APPS
```

## 🔧 Configurações Personalizadas

### Arquivo: `config/settings.py`

```python
# Django Extensions Settings
SHELL_PLUS = "ipython"  # Usa IPython por padrão
SHELL_PLUS_PRINT_SQL = False  # Exibir SQL? (True/False)

# Importar automaticamente no shell_plus
SHELL_PLUS_PRE_IMPORTS = [
    ('datetime', ('datetime', 'date', 'timedelta')),
    ('decimal', 'Decimal'),
]

# Modelos a importar automaticamente
SHELL_PLUS_MODEL_ALIASES = {
    'finances': {
        'Transaction': 'Tx',
        'Category': 'Cat',
    }
}
```

### Configuração Avançada (Opcional)

Adicione ao `settings.py` se quiser mais customizações:

```python
# Shell Plus com imports extras
SHELL_PLUS_PRE_IMPORTS = [
    ('datetime', ('datetime', 'date', 'timedelta')),
    ('decimal', 'Decimal'),
    ('django.db.models', ('Q', 'F', 'Count', 'Sum', 'Avg')),
]

# Shell Plus com código inicial
SHELL_PLUS_POST_IMPORTS = [
    ('finances.services.invoice_service', 'InvoiceService'),
    ('finances.services.recurring_service', 'RecurringService'),
]
```

## 💡 Dicas e Truques

### 1. Atalhos do IPython

- `Ctrl + A` - Ir para o início da linha
- `Ctrl + E` - Ir para o fim da linha
- `Ctrl + K` - Deletar do cursor até o fim
- `Ctrl + U` - Deletar do cursor até o início
- `Ctrl + L` - Limpar tela
- `Ctrl + D` - Sair do shell

### 2. Executar Código Python Externo

```python
# No shell_plus
%run /caminho/para/script.py
```

### 3. Debug Interativo

```python
# Adicione ao seu código
import ipdb; ipdb.set_trace()
# ou
breakpoint()  # Python 3.7+
```

### 4. Exportar Dados

```python
# Exportar para CSV
>>> import csv
>>> with open('transactions.csv', 'w') as f:
...     writer = csv.writer(f)
...     for t in Transaction.objects.all():
...         writer.writerow([t.id, t.description, t.amount])
```

### 5. Análise Rápida

```python
# Ver estatísticas
>>> Transaction.objects.aggregate(
...     total=Sum('amount'),
...     avg=Avg('amount'),
...     count=Count('id')
... )
```

## 🎓 Comandos Shell vs Shell Plus

### Shell Padrão (antigo)
```bash
$ python manage.py shell
>>> from finances.models import Transaction
>>> from accounts.models import User
>>> # ... muitos imports manuais
```

### Shell Plus (novo)
```bash
$ python manage.py shell_plus
# Tudo já importado automaticamente! ✨
>>> Transaction.objects.all()
>>> User.objects.all()
```

## 📚 Documentação

- **Django Extensions**: https://django-extensions.readthedocs.io/
- **IPython**: https://ipython.readthedocs.io/
- **Magic Commands**: https://ipython.readthedocs.io/en/stable/interactive/magics.html

## ✅ Checklist de Instalação

- ✅ django-extensions instalado
- ✅ ipython instalado
- ✅ django_extensions adicionado ao INSTALLED_APPS
- ✅ SHELL_PLUS = "ipython" configurado
- ✅ requirements.txt atualizado
- ✅ Pronto para usar!

## 🚀 Comece Agora!

```bash
# Ative o virtualenv (se ainda não estiver)
source ~/.pyenv/versions/mydindin/bin/activate

# Ou com pyenv
pyenv activate mydindin

# Inicie o shell plus
python manage.py shell_plus

# Divirta-se! 🎉
```

---

**Desenvolvido para aumentar sua produtividade! 🚀**

