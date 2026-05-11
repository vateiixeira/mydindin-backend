"""
Script para testar se os signals estão sendo disparados com bulk_create/bulk_update.
"""

import os
import django
from decimal import Decimal
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from finances.models import Category, InstallmentPlan, Installment, Transaction, CreditCard
from finances.services.invoice_service import InvoiceService

User = get_user_model()


def test_bulk_vs_individual():
    """
    Testa se bulk_create/bulk_update disparam signals vs criação individual.
    """
    print("\n" + "="*70)
    print("TESTE: Signals com bulk_create vs criação individual")
    print("="*70)
    
    # 1. Criar dados de teste
    user, _ = User.objects.get_or_create(
        email='teste@teste.com',
        defaults={'name': 'Usuário Teste', 'is_active': True}
    )
    
    category, _ = Category.objects.get_or_create(
        name='Teste Signals',
        type='expense',
        user=user
    )
    
    credit_card, _ = CreditCard.objects.get_or_create(
        user=user,
        name='Nubank Teste',
        defaults={
            'brand': 'mastercard',
            'due_day': 10,
            'closing_day': 5
        }
    )
    
    print(f"\n✓ Usuário: {user.email}")
    print(f"✓ Categoria: {category.name}")
    print(f"✓ Cartão: {credit_card.name}")
    
    # 2. Teste 1: Criar Installment individualmente (deve disparar signal)
    print(f"\n🧪 TESTE 1: Criar Installment individualmente")
    print("-" * 50)
    
    # Criar um plano pequeno
    plan1 = InstallmentPlan.objects.create(
        user=user,
        category=category,
        type='expense',
        description='Teste Individual - 1x',
        credit_card=credit_card,
        total_installments=1,
        default_amount=Decimal('100.00'),
        start_date=date.today()
    )
    
    # Aguardar um pouco para processar
    import time
    time.sleep(2)
    
    # Verificar se a parcela foi vinculada à fatura
    installment1 = plan1.installments.first()
    if installment1:
        print(f"Parcela criada: ID {installment1.id}")
        print(f"Tem cartão? {installment1.plan.credit_card is not None}")
        print(f"Tem fatura? {installment1.invoice is not None}")
        if installment1.invoice:
            print(f"Fatura: {installment1.invoice}")
        else:
            print("❌ Parcela NÃO foi vinculada à fatura!")
    else:
        print("❌ Nenhuma parcela foi criada!")
    
    # 3. Teste 2: Verificar se o problema é no bulk_create
    print(f"\n🧪 TESTE 2: Verificar bulk_create")
    print("-" * 50)
    
    # Criar Installment manualmente (sem bulk)
    installment_manual = Installment.objects.create(
        plan=plan1,
        installment_number=2,
        amount=Decimal('200.00'),
        due_date=date.today(),
        status='pending'
    )
    
    print(f"Parcela manual criada: ID {installment_manual.id}")
    print(f"Tem cartão? {installment_manual.plan.credit_card is not None}")
    print(f"Tem fatura? {installment_manual.invoice is not None}")
    if installment_manual.invoice:
        print(f"Fatura: {installment_manual.invoice}")
        print("✅ Signal foi disparado!")
    else:
        print("❌ Signal NÃO foi disparado!")
    
    # 4. Teste 3: Verificar se o problema é no bulk_update
    print(f"\n🧪 TESTE 3: Verificar bulk_update")
    print("-" * 50)
    
    # Atualizar a parcela manual (deve disparar signal)
    installment_manual.status = 'generated'
    installment_manual.save()
    
    print(f"Parcela atualizada: status = {installment_manual.status}")
    print(f"Tem fatura? {installment_manual.invoice is not None}")
    if installment_manual.invoice:
        print(f"Fatura: {installment_manual.invoice}")
        print("✅ Signal foi disparado na atualização!")
    else:
        print("❌ Signal NÃO foi disparado na atualização!")
    
    # 5. Teste 4: Chamar o método manualmente
    print(f"\n🧪 TESTE 4: Chamar método manualmente")
    print("-" * 50)
    
    if not installment_manual.invoice:
        print("Chamando link_installment_to_invoice manualmente...")
        service = InvoiceService()
        invoice = service.link_installment_to_invoice(installment_manual)
        
        if invoice:
            print(f"✅ Fatura criada/vincular manualmente: {invoice}")
            installment_manual.refresh_from_db()
            print(f"Parcela tem fatura? {installment_manual.invoice is not None}")
        else:
            print("❌ Não foi possível vincular à fatura")
    
    # 6. Verificar faturas existentes
    print(f"\n🧪 TESTE 5: Verificar faturas existentes")
    print("-" * 50)
    
    from finances.models import CreditCardInvoice
    invoices = CreditCardInvoice.objects.filter(credit_card=credit_card)
    print(f"Faturas existentes para o cartão: {invoices.count()}")
    for invoice in invoices:
        print(f"  - {invoice} (referência: {invoice.reference_month})")
    
    print("\n" + "="*70)
    print("DIAGNÓSTICO:")
    
    if installment1 and installment1.invoice:
        print("✅ Parcelas criadas via bulk_create TÊM fatura vinculada")
    else:
        print("❌ Parcelas criadas via bulk_create NÃO têm fatura vinculada")
        print("   → O problema é que bulk_create NÃO dispara signals!")
    
    if installment_manual and installment_manual.invoice:
        print("✅ Parcelas criadas individualmente TÊM fatura vinculada")
    else:
        print("❌ Parcelas criadas individualmente NÃO têm fatura vinculada")
        print("   → O problema é mais profundo!")
    
    print("="*70 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        test_bulk_vs_individual()
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
