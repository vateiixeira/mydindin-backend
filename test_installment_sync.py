"""
Script de teste para validar a sincronização automática entre parcelas e transações.

Execute com:
    python test_installment_sync.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from finances.models import Category, InstallmentPlan, Installment, Transaction

User = get_user_model()


def test_installment_amount_sync():
    """
    Testa se a atualização do amount da parcela sincroniza com a transação.
    """
    print("\n" + "="*60)
    print("TESTE: Sincronização de Amount entre Parcela e Transação")
    print("="*60)
    
    # 1. Obter ou criar um usuário de teste
    user, _ = User.objects.get_or_create(
        email='teste@teste.com',
        defaults={
            'name': 'Usuário Teste',
            'is_active': True
        }
    )
    print(f"\n✓ Usuário: {user.email}")
    
    # 2. Obter ou criar uma categoria de despesa
    category, _ = Category.objects.get_or_create(
        name='Teste Financiamento',
        type='expense',
        user=user
    )
    print(f"✓ Categoria: {category.name}")
    
    # 3. Criar um plano de parcelamento
    plan, created = InstallmentPlan.objects.get_or_create(
        user=user,
        category=category,
        type='expense',
        description='Teste de Sincronização',
        defaults={
            'total_installments': 3,
            'default_amount': Decimal('100.00'),
            'start_date': '2024-10-01'
        }
    )
    
    if created:
        print(f"✓ Plano criado: {plan.description} ({plan.total_installments}x)")
        # Gerar parcelas
        from finances.services.installment_service import InstallmentService
        InstallmentService.generate_installments(plan)
        print(f"✓ Parcelas geradas: {plan.installments.count()}")
    else:
        print(f"✓ Plano existente: {plan.description}")
    
    # 4. Pegar a primeira parcela
    installment = plan.installments.first()
    print(f"\n📦 Parcela #{installment.id}:")
    print(f"   - Amount inicial: R$ {installment.amount}")
    print(f"   - Status: {installment.status}")
    print(f"   - Transaction ID: {installment.transaction_id}")
    
    # 5. Criar uma transação vinculada manualmente (simulando que foi gerada)
    if not installment.transaction:
        transaction = Transaction.objects.create(
            user=user,
            category=category,
            type='expense',
            description=f'Parcela {installment.installment_number}/{plan.total_installments} - {plan.description}',
            amount=installment.amount,
            transaction_date=installment.due_date,
            status='pending'
        )
        installment.transaction = transaction
        installment.status = 'generated'
        installment.save()
        print(f"\n✓ Transação criada e vinculada: Transaction #{transaction.id}")
    
    transaction = installment.transaction
    print(f"\n💰 Transação #{transaction.id}:")
    print(f"   - Amount inicial: R$ {transaction.amount}")
    print(f"   - Description: {transaction.description}")
    
    # 6. Atualizar o amount da parcela
    new_amount = Decimal('150.00')
    print(f"\n🔄 Atualizando parcela de R$ {installment.amount} para R$ {new_amount}...")
    
    old_installment_amount = installment.amount
    old_transaction_amount = transaction.amount
    
    installment.amount = new_amount
    installment.save()
    
    # 7. Verificar se a transação foi atualizada
    transaction.refresh_from_db()
    
    print(f"\n📊 RESULTADO:")
    print(f"   Parcela:")
    print(f"      - Amount anterior: R$ {old_installment_amount}")
    print(f"      - Amount atual: R$ {installment.amount}")
    print(f"   ")
    print(f"   Transação:")
    print(f"      - Amount anterior: R$ {old_transaction_amount}")
    print(f"      - Amount atual: R$ {transaction.amount}")
    
    # NOTA: O teste via .save() não aciona o perform_update da ViewSet!
    # A sincronização só acontece via API (PATCH request)
    print(f"\n⚠️  IMPORTANTE:")
    print(f"   Este teste cria os dados, mas a sincronização automática")
    print(f"   só funciona através da API (PATCH /api/installments/{{id}}/).")
    print(f"   ")
    print(f"   Para testar a sincronização real, use:")
    print(f"   ")
    print(f"   curl -X PATCH \\")
    print(f"     -H 'Authorization: Bearer TOKEN' \\")
    print(f"     -H 'Content-Type: application/json' \\")
    print(f"     -d '{{\"amount\": 200.00}}' \\")
    print(f"     http://localhost:8000/api/installments/{installment.id}/")
    
    print("\n" + "="*60)
    print("✅ Dados de teste criados com sucesso!")
    print("="*60)
    
    return {
        'installment_id': installment.id,
        'transaction_id': transaction.id,
        'plan_id': plan.id,
        'user_email': user.email
    }


def show_api_test_commands(data):
    """
    Mostra comandos para testar via API.
    """
    print(f"\n📋 COMANDOS PARA TESTAR VIA API:")
    print(f"\n1. Ver estado atual da parcela:")
    print(f"   GET /api/installments/{data['installment_id']}/")
    
    print(f"\n2. Atualizar o amount da parcela (isso vai sincronizar a transação):")
    print(f"   PATCH /api/installments/{data['installment_id']}/")
    print(f"   Body: {{\"amount\": 200.00}}")
    
    print(f"\n3. Verificar se a transação foi sincronizada:")
    print(f"   GET /api/transactions/{data['transaction_id']}/")
    print(f"   (O amount deve ser igual ao da parcela)")
    
    print(f"\n4. Ver o plano completo:")
    print(f"   GET /api/installment-plans/{data['plan_id']}/")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    try:
        data = test_installment_amount_sync()
        show_api_test_commands(data)
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

