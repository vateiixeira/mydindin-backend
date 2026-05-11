# ✅ Django Extensions + IPython - Instalado com Sucesso!

## 📦 Pacotes Instalados

```bash
✅ django-extensions==4.1
✅ ipython==9.6.0
```

## ⚙️ Configurações Aplicadas

### 1. `config/settings.py`

```python
INSTALLED_APPS = [
    ...
    'django_extensions',  # ← Adicionado
    ...
]

# Django Extensions Settings
SHELL_PLUS = "ipython"  # ← Usa IPython por padrão
SHELL_PLUS_PRINT_SQL = False  # ← Ver SQL queries (False por padrão)
```

### 2. `requirements.txt`

```
django-extensions==4.1
ipython==9.6.0
```

## 🚀 Como Usar

### Shell Plus (Recomendado)

```bash
# Ativar virtualenv
pyenv activate mydindin

# Iniciar shell plus com IPython
python manage.py shell_plus
```

**Vantagens**:
- ✅ Todos os modelos já importados (User, Transaction, Category, etc.)
- ✅ IPython com autocomplete avançado
- ✅ Sintaxe colorida
- ✅ Histórico persistente
- ✅ Magic commands (%timeit, %history, etc.)

### Exemplo Rápido

```python
$ python manage.py shell_plus

# Modelos já estão importados!
>>> User.objects.count()
3

>>> Transaction.objects.filter(type='income')
<QuerySet [...]>

>>> Category.objects.all()
<QuerySet [...]>

# Magic commands do IPython
>>> %timeit User.objects.count()
142 µs ± 3.52 µs per loop

# Autocomplete com TAB
>>> User.objects.f<TAB>
User.objects.filter(
User.objects.first(
```

## 📋 Comandos Úteis

### Ver todas as URLs
```bash
python manage.py show_urls
python manage.py show_urls | grep api
```

### Ver queries SQL no shell
```bash
python manage.py shell_plus --print-sql
```

### Limpar arquivos .pyc
```bash
python manage.py clean_pyc
```

### Validar templates
```bash
python manage.py validate_templates
```

## 📚 Documentação Completa

Para mais detalhes, consulte: **`DJANGO_EXTENSIONS_IPYTHON.md`**

Contém:
- ✅ Todos os comandos disponíveis
- ✅ Magic commands do IPython
- ✅ Exemplos práticos
- ✅ Dicas e truques
- ✅ Configurações avançadas

## 🎯 Teste Agora!

```bash
# 1. Ative o virtualenv
pyenv activate mydindin

# 2. Inicie o shell plus
python manage.py shell_plus

# 3. Teste os modelos
>>> User.objects.all()
>>> Transaction.objects.count()
>>> Category.objects.filter(type='income')

# 4. Use os magic commands
>>> %history
>>> %timeit Category.objects.count()

# 5. Saia com Ctrl+D ou
>>> exit()
```

## ✅ Status

- ✅ Instalação completa
- ✅ Configuração aplicada
- ✅ Pronto para uso!

---

**Instalado e configurado com sucesso! 🎉**

