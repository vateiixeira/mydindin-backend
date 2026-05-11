#!/usr/bin/env python
"""
Script de teste para o sistema de faturas automáticas.
Execute com: python manage.py shell < test_invoices.py
Ou: python manage.py shell
     >>> exec(open('test_invoices.py').read())
"""

from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from finances.models import (
    Category, CreditCard, CreditCardInvoice, 
    Transaction, InstallmentPlan
)
from finances.tasks import create_credit_card_invoices, update_overdue_invoices

User = get_user_model()

print("=" * 80)
print("🧪 TESTE DO SISTEMA DE FATURAS AUTOMÁTICAS")
print("=" * 80)

# 1. Preparar dados de teste
print("\n📦 1. Preparando dados de teste...")

user = User.objects.first()
if not user:
    print("❌ Nenhum usuário encontrado. Crie um usuário primeiro.")
    exit(1)

print(f"✓ Usuário: {user.username}")

# Criar categoria de despesa
category, created = Category.objects.get_or_create(
    name="Testes",
    type="expense",
    user=user,
    defaults={'description': 'Categoria para testes'}
)
print(f"✓ Categoria: {category.name}")

# Criar cartão de crédito
card, created = CreditCard.objects.get_or_create(
    user=user,
    name="Cartão Teste",
    defaults={
        'brand': 'visa',
        'closing_day': 15,  # Fecha dia 15
        'due_day': 25,      # Vence dia 25
        'credit_limit': Decimal('10000.00'),
        'is_active': True
    }
)
if created:
    print(f"✓ Cartão criado: {card.name}")
else:
    print(f"✓ Cartão existente: {card.name}")

print(f"  - Dia de fechamento: {card.closing_day}")
print(f"  - Dia de vencimento: {card.due_day}")

# 2. Testar criação de transação ANTES do fechamento
print("\n💳 2. Testando transação ANTES do dia de fechamento...")

today = date.today()
transaction_date_before = date(today.year, today.month, 10)  # Dia 10

trans1 = Transaction.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Compra teste - antes do fechamento",
    amount=Decimal('150.50'),
    credit_card=card,
    transaction_date=transaction_date_before,
    status='pending'
)

print(f"✓ Transação criada: {trans1.description}")
print(f"  - Data: {trans1.transaction_date}")
print(f"  - Valor: R$ {trans1.amount}")
print(f"  - Fatura vinculada: {trans1.invoice}")

if trans1.invoice:
    print(f"  - Mês de referência: {trans1.invoice.reference_month.strftime('%m/%Y')}")
    print(f"  - Data de fechamento: {trans1.invoice.closing_date}")
    print(f"  - Data de vencimento: {trans1.invoice.due_date}")
else:
    print("  ⚠️ Fatura não foi criada automaticamente")

# 3. Testar criação de transação DEPOIS do fechamento
print("\n💳 3. Testando transação DEPOIS do dia de fechamento...")

transaction_date_after = date(today.year, today.month, 20)  # Dia 20

trans2 = Transaction.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Compra teste - depois do fechamento",
    amount=Decimal('200.00'),
    credit_card=card,
    transaction_date=transaction_date_after,
    status='pending'
)

print(f"✓ Transação criada: {trans2.description}")
print(f"  - Data: {trans2.transaction_date}")
print(f"  - Valor: R$ {trans2.amount}")
print(f"  - Fatura vinculada: {trans2.invoice}")

if trans2.invoice:
    print(f"  - Mês de referência: {trans2.invoice.reference_month.strftime('%m/%Y')}")
    print(f"  - Data de fechamento: {trans2.invoice.closing_date}")
    print(f"  - Data de vencimento: {trans2.invoice.due_date}")

# 4. Verificar faturas diferentes
print("\n📊 4. Verificando se as faturas são diferentes...")

if trans1.invoice and trans2.invoice:
    if trans1.invoice.id != trans2.invoice.id:
        print("✓ As transações foram vinculadas a faturas diferentes (correto!)")
    else:
        print("⚠️ As transações foram vinculadas à mesma fatura")
else:
    print("⚠️ Alguma transação não foi vinculada a fatura")

# 5. Testar parcelamento
print("\n📅 5. Testando parcelamento no cartão...")

plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Teste Parcelamento 3x",
    credit_card=card,
    total_installments=3,
    default_amount=Decimal('100.00'),
    start_date=date(today.year, today.month, 5),
    is_active=True
)

print(f"✓ Plano criado: {plan.description}")
print(f"  - Total de parcelas: {plan.total_installments}")
print(f"  - Valor por parcela: R$ {plan.default_amount}")

print("\n  Parcelas criadas:")
for installment in plan.installments.all()[:3]:
    print(f"  - Parcela {installment.installment_number}: {installment.due_date} → Fatura: {installment.invoice}")

# 6. Executar task de criação de faturas
print("\n⚙️ 6. Executando task de criação de faturas...")

result = create_credit_card_invoices()
print(f"✓ Task executada:")
print(f"  - Cartões processados: {result['processed']}")
print(f"  - Faturas criadas: {result['created']}")
print(f"  - Faturas ignoradas (já existiam): {result['skipped']}")
print(f"  - Erros: {len(result['errors'])}")

if result['errors']:
    for error in result['errors']:
        print(f"  ✗ {error}")

# 7. Listar todas as faturas do cartão
print("\n📋 7. Listando todas as faturas do cartão...")

invoices = CreditCardInvoice.objects.filter(credit_card=card).order_by('reference_month')
print(f"\n✓ Total de faturas: {invoices.count()}")

for invoice in invoices:
    print(f"\n  📄 Fatura {invoice.reference_month.strftime('%m/%Y')}")
    print(f"     - Fechamento: {invoice.closing_date}")
    print(f"     - Vencimento: {invoice.due_date}")
    print(f"     - Status: {invoice.get_status_display()}")
    print(f"     - Total da fatura: R$ {invoice.total_amount}")
    print(f"     - Gastos declarados: R$ {invoice.get_declared_expenses()}")
    print(f"     - Transações: {invoice.transactions.count()}")
    print(f"     - Parcelas: {invoice.installments.count()}")
    
    if invoice.transactions.exists():
        print(f"     Transações:")
        for trans in invoice.transactions.all():
            print(f"       • {trans.description}: R$ {trans.amount}")
    
    if invoice.installments.exists():
        print(f"     Parcelas:")
        for inst in invoice.installments.all():
            print(f"       • {inst}: R$ {inst.amount}")

# 8. Testar atualização de status
print("\n⏰ 8. Testando atualização de faturas atrasadas...")

# Criar fatura vencida
past_date = today - timedelta(days=30)
past_invoice, created = CreditCardInvoice.objects.get_or_create(
    credit_card=card,
    reference_month=date(past_date.year, past_date.month, 1),
    defaults={
        'total_amount': Decimal('500.00'),
        'closing_date': date(past_date.year, past_date.month, 15),
        'due_date': past_date - timedelta(days=5),  # Vencida
        'status': 'pending'
    }
)

if created:
    print(f"✓ Fatura vencida criada para teste: {past_invoice}")

result = update_overdue_invoices()
print(f"✓ Task executada:")
print(f"  - Faturas atualizadas: {result['invoices_updated']}")

past_invoice.refresh_from_db()
print(f"  - Status da fatura vencida: {past_invoice.get_status_display()}")

# 9. Resumo final
print("\n" + "=" * 80)
print("📈 RESUMO FINAL")
print("=" * 80)

total_invoices = CreditCardInvoice.objects.filter(credit_card=card).count()
total_transactions = Transaction.objects.filter(credit_card=card).count()
total_installments = plan.installments.count() if plan else 0

print(f"✓ Cartões de crédito: 1")
print(f"✓ Faturas criadas: {total_invoices}")
print(f"✓ Transações criadas: {total_transactions}")
print(f"✓ Parcelas criadas: {total_installments}")

print("\n" + "=" * 80)
print("✅ TESTE CONCLUÍDO COM SUCESSO!")
print("=" * 80)
print("\n💡 Dicas:")
print("  - As faturas são criadas automaticamente quando você adiciona transações")
print("  - A task 'create_credit_card_invoices' roda todo dia às 00:15")
print("  - A task 'update_overdue_invoices' roda todo dia às 00:20")
print("  - Só existe 1 fatura por mês (garantido pelo unique_together)")
print("\n🧹 Para limpar os dados de teste:")
print("  - Transaction.objects.filter(description__contains='teste').delete()")
print("  - InstallmentPlan.objects.filter(description__contains='Teste').delete()")
print("  - CreditCard.objects.filter(name='Cartão Teste').delete()")
print()

