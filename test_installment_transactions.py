#!/usr/bin/env python
"""
Script de teste para validar criação automática de transações ao criar InstallmentPlan.
Execute com: python manage.py shell < test_installment_transactions.py
"""

from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from finances.models import (
    Category, CreditCard, InstallmentPlan, 
    Transaction, Installment, CreditCardInvoice
)

User = get_user_model()

print("=" * 80)
print("🧪 TESTE - CRIAÇÃO AUTOMÁTICA DE TRANSAÇÕES NO PARCELAMENTO")
print("=" * 80)

# 1. Preparar dados
print("\n📦 1. Preparando dados de teste...")

user = User.objects.first()
if not user:
    print("❌ Nenhum usuário encontrado. Crie um usuário primeiro.")
    exit(1)

print(f"✓ Usuário: {user.username}")

# Criar categoria
category, _ = Category.objects.get_or_create(
    name="Eletrônicos",
    type="expense",
    user=user,
    defaults={'description': 'Categoria para eletrônicos'}
)
print(f"✓ Categoria: {category.name}")

# Criar cartão de crédito
card, created = CreditCard.objects.get_or_create(
    user=user,
    name="Cartão Teste Parcelamento",
    defaults={
        'brand': 'visa',
        'closing_day': 15,
        'due_day': 25,
        'credit_limit': Decimal('10000.00'),
        'is_active': True
    }
)
if created:
    print(f"✓ Cartão criado: {card.name}")
else:
    print(f"✓ Cartão existente: {card.name}")

# 2. Criar parcelamento COM cartão de crédito
print("\n💳 2. Criando parcelamento de 6x COM cartão de crédito...")

plan = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Notebook Dell 6x",
    credit_card=card,  # ← Vinculado ao cartão
    total_installments=6,
    default_amount=Decimal('500.00'),
    start_date=date(2025, 11, 5),  # Primeira parcela em 05/11/2025
    is_active=True
)

print(f"✓ Plano criado: {plan.description}")
print(f"  - Total de parcelas: {plan.total_installments}")
print(f"  - Valor por parcela: R$ {plan.default_amount}")
print(f"  - Cartão: {plan.credit_card.name}")

# 3. Verificar parcelas criadas
print("\n📊 3. Verificando parcelas criadas...")

installments = plan.installments.all().order_by('installment_number')
print(f"✓ Total de parcelas criadas: {installments.count()}")

if installments.count() != plan.total_installments:
    print(f"❌ ERRO: Esperado {plan.total_installments} parcelas, mas foram criadas {installments.count()}")
else:
    print(f"✓ Correto: {plan.total_installments} parcelas criadas")

# 4. Verificar transações criadas
print("\n💰 4. Verificando transações criadas automaticamente...")

transactions_count = Transaction.objects.filter(
    notes__icontains=f"parcelamento {plan.description}"
).count()

print(f"✓ Total de transações criadas: {transactions_count}")

if transactions_count != plan.total_installments:
    print(f"⚠️ ALERTA: Esperado {plan.total_installments} transações, mas foram criadas {transactions_count}")
else:
    print(f"✓ Correto: {plan.total_installments} transações criadas")

# 5. Verificar vinculação parcela <-> transação
print("\n🔗 5. Verificando vinculação parcela ↔ transação...")

all_linked = True
for installment in installments:
    if not installment.transaction:
        print(f"❌ Parcela {installment.installment_number} NÃO tem transação vinculada")
        all_linked = False

if all_linked:
    print(f"✓ Todas as {installments.count()} parcelas têm transações vinculadas")

# 6. Verificar status das parcelas
print("\n📋 6. Verificando status das parcelas...")

generated_count = installments.filter(status='generated').count()
print(f"✓ Parcelas com status 'generated': {generated_count}/{installments.count()}")

if generated_count == installments.count():
    print("✓ Todas as parcelas têm status 'generated' (correto!)")
else:
    print(f"⚠️ Nem todas as parcelas têm status 'generated'")

# 7. Verificar faturas criadas
print("\n🧾 7. Verificando faturas criadas automaticamente...")

# As transações têm cartão, então os signals devem ter criado faturas
invoices = CreditCardInvoice.objects.filter(credit_card=card)
print(f"✓ Total de faturas criadas: {invoices.count()}")

# 8. Verificar vinculação transação -> fatura
print("\n🎯 8. Verificando vinculação transação → fatura...")

transactions_with_invoice = 0
transactions_with_card = Transaction.objects.filter(
    notes__icontains=f"parcelamento {plan.description}"
)

for trans in transactions_with_card:
    if trans.invoice:
        transactions_with_invoice += 1

print(f"✓ Transações vinculadas a faturas: {transactions_with_invoice}/{transactions_with_card.count()}")

if transactions_with_invoice == transactions_with_card.count():
    print("✓ Todas as transações foram vinculadas a faturas (correto!)")
else:
    print(f"⚠️ Apenas {transactions_with_invoice} de {transactions_with_card.count()} foram vinculadas")

# 9. Listar detalhes de cada parcela
print("\n📝 9. Detalhes de cada parcela criada:")

for installment in installments[:3]:  # Mostrar apenas 3 primeiras
    print(f"\n  Parcela {installment.installment_number}/{plan.total_installments}:")
    print(f"    - Vencimento: {installment.due_date}")
    print(f"    - Valor: R$ {installment.amount}")
    print(f"    - Status: {installment.get_status_display()}")
    print(f"    - Transação: {installment.transaction.id if installment.transaction else 'N/A'}")
    
    if installment.transaction:
        print(f"      • Descrição: {installment.transaction.description}")
        print(f"      • Data: {installment.transaction.transaction_date}")
        print(f"      • Cartão: {installment.transaction.credit_card.name if installment.transaction.credit_card else 'N/A'}")
        print(f"      • Fatura: {installment.transaction.invoice if installment.transaction.invoice else 'N/A'}")
    
    if installment.invoice:
        print(f"    - Fatura (parcela): {installment.invoice}")

if installments.count() > 3:
    print(f"\n  ... e mais {installments.count() - 3} parcelas")

# 10. Testar parcelamento SEM cartão
print("\n" + "=" * 80)
print("💳 10. Testando parcelamento SEM cartão de crédito...")

plan_no_card = InstallmentPlan.objects.create(
    user=user,
    category=category,
    type='expense',
    description="Móveis 12x (sem cartão)",
    credit_card=None,  # ← SEM cartão
    total_installments=12,
    default_amount=Decimal('300.00'),
    start_date=date(2025, 11, 10),
    is_active=True
)

print(f"✓ Plano criado (sem cartão): {plan_no_card.description}")

installments_no_card = plan_no_card.installments.all()
print(f"✓ Parcelas criadas: {installments_no_card.count()}")

transactions_no_card = Transaction.objects.filter(
    notes__icontains=f"parcelamento {plan_no_card.description}"
)
print(f"✓ Transações criadas: {transactions_no_card.count()}")

# Verificar que transações NÃO têm cartão
trans_with_card = transactions_no_card.filter(credit_card__isnull=False).count()
print(f"✓ Transações COM cartão: {trans_with_card}")
print(f"✓ Transações SEM cartão: {transactions_no_card.count() - trans_with_card}")

if trans_with_card == 0:
    print("✓ Correto: Nenhuma transação tem cartão vinculado")

# Verificar que transações NÃO têm fatura
trans_with_invoice = transactions_no_card.filter(invoice__isnull=False).count()
print(f"✓ Transações COM fatura: {trans_with_invoice}")
print(f"✓ Transações SEM fatura: {transactions_no_card.count() - trans_with_invoice}")

if trans_with_invoice == 0:
    print("✓ Correto: Nenhuma transação tem fatura vinculada (sem cartão)")

# 11. Resumo final
print("\n" + "=" * 80)
print("📊 RESUMO FINAL")
print("=" * 80)

total_plans = 2
total_installments = plan.total_installments + plan_no_card.total_installments
total_transactions = Transaction.objects.filter(
    notes__icontains="parcelamento"
).count()

print(f"\n✓ Planos de parcelamento criados: {total_plans}")
print(f"  - Com cartão: 1 ({plan.total_installments}x)")
print(f"  - Sem cartão: 1 ({plan_no_card.total_installments}x)")

print(f"\n✓ Total de parcelas criadas: {total_installments}")
print(f"✓ Total de transações criadas: {total_transactions}")

if total_transactions == total_installments:
    print(f"✓ Correto: 1 transação para cada parcela")
else:
    print(f"⚠️ Inconsistência: {total_installments} parcelas mas {total_transactions} transações")

print(f"\n✓ Faturas criadas automaticamente: {invoices.count()}")

# Verificação final
print("\n" + "=" * 80)
print("✅ VERIFICAÇÃO FINAL")
print("=" * 80)

checks = {
    "Parcelas criadas corretamente": installments.count() == plan.total_installments,
    "Transações criadas para todas as parcelas": transactions_count == plan.total_installments,
    "Todas as parcelas têm transação vinculada": all_linked,
    "Status das parcelas é 'generated'": generated_count == installments.count(),
    "Transações com cartão têm fatura": transactions_with_invoice == transactions_with_card.count(),
    "Parcelamento sem cartão funciona": transactions_no_card.count() == plan_no_card.total_installments,
}

all_passed = True
for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check}")
    if not passed:
        all_passed = False

if all_passed:
    print("\n" + "=" * 80)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("=" * 80)
    print("\n✅ Sistema funcionando corretamente:")
    print("   1. Parcelas são criadas automaticamente")
    print("   2. Transações são criadas automaticamente para cada parcela")
    print("   3. Parcelas são vinculadas às transações")
    print("   4. Transações com cartão são vinculadas a faturas automaticamente")
    print("   5. Status das parcelas é atualizado para 'generated'")
else:
    print("\n⚠️ Alguns testes falharam. Verifique os detalhes acima.")

print("\n🧹 Para limpar os dados de teste:")
print("   InstallmentPlan.objects.filter(description__icontains='Notebook Dell').delete()")
print("   InstallmentPlan.objects.filter(description__icontains='Móveis').delete()")
print("   CreditCard.objects.filter(name='Cartão Teste Parcelamento').delete()")
print()

