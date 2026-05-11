"""
Script para testar a deleção em cascata de InstallmentPlan.

Quando deletar um InstallmentPlan, deve deletar:
- Todos os Installments
- Todas as Transactions vinculadas

Execute com:
    python test_cascade_delete.py
"""

import os
import django
from decimal import Decimal
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from finances.models import Category, InstallmentPlan, Installment, Transaction

User = get_user_model()


def test_cascade_delete():
    """
    Testa a deleção em cascata de InstallmentPlan.
    """
    print("\n" + "="*70)
    print("TESTE: Deleção em Cascata de InstallmentPlan")
    print("="*70)
    
    # 1. Obter ou criar um usuário de teste
    user, _ = User.objects.get_or_create(
        email='teste@teste.com',
        defaults={
            'name': 'Usuário Teste',
            'is_active': True
        }
    )
    print(f"\n✓ Usuário: {user.email}")
    
    # 2. Obter ou criar uma categoria
    category, _ = Category.objects.get_or_create(
        name='Teste Deleção',
        type='expense',
        user=user
    )
    print(f"✓ Categoria: {category.name}")
    
    # 3. Estatísticas ANTES de criar
    stats_initial = {
        'plans': InstallmentPlan.objects.count(),
        'installments': Installment.objects.count(),
        'transactions': Transaction.objects.count()
    }
    print(f"\n📊 ESTATÍSTICAS INICIAIS:")
    print(f"   - Planos: {stats_initial['plans']}")
    print(f"   - Parcelas: {stats_initial['installments']}")
    print(f"   - Transações: {stats_initial['transactions']}")
    
    # 4. Criar um plano de parcelamento
    plan = InstallmentPlan.objects.create(
        user=user,
        category=category,
        type='expense',
        description='Teste Deleção Cascata - 5x',
        total_installments=5,
        default_amount=Decimal('200.00'),
        start_date=date.today()
    )
    
    plan_id = plan.id
    print(f"\n✓ Plano criado: ID {plan_id}")
    print(f"  - Descrição: {plan.description}")
    print(f"  - Total de parcelas: {plan.total_installments}")
    
    # 5. Aguardar criação de parcelas e transações (automático)
    import time
    time.sleep(1)  # Dar tempo para signals processarem
    
    # 6. Coletar IDs das parcelas e transações
    installments = list(plan.installments.all())
    installment_ids = [inst.id for inst in installments]
    transaction_ids = []
    
    print(f"\n📦 PARCELAS CRIADAS:")
    for inst in installments:
        print(f"   - Parcela {inst.installment_number}: ID {inst.id}")
        if inst.transaction:
            transaction_ids.append(inst.transaction.id)
            print(f"     → Transação: ID {inst.transaction.id}")
    
    # 7. Estatísticas APÓS criar
    stats_after_create = {
        'plans': InstallmentPlan.objects.count(),
        'installments': Installment.objects.count(),
        'transactions': Transaction.objects.count()
    }
    print(f"\n📊 ESTATÍSTICAS APÓS CRIAR:")
    print(f"   - Planos: {stats_after_create['plans']} (+{stats_after_create['plans'] - stats_initial['plans']})")
    print(f"   - Parcelas: {stats_after_create['installments']} (+{stats_after_create['installments'] - stats_initial['installments']})")
    print(f"   - Transações: {stats_after_create['transactions']} (+{stats_after_create['transactions'] - stats_initial['transactions']})")
    
    # 8. Verificar existência antes de deletar
    print(f"\n🔍 VERIFICAÇÃO ANTES DE DELETAR:")
    print(f"   - Plano {plan_id} existe? {InstallmentPlan.objects.filter(id=plan_id).exists()}")
    print(f"   - Parcelas existem? {Installment.objects.filter(id__in=installment_ids).exists()}")
    print(f"   - Transações existem? {Transaction.objects.filter(id__in=transaction_ids).exists()}")
    
    # 9. DELETAR O PLANO
    print(f"\n🗑️  DELETANDO PLANO {plan_id}...")
    print("-" * 70)
    plan.delete()
    print("-" * 70)
    
    # 10. Verificar existência após deletar
    print(f"\n🔍 VERIFICAÇÃO APÓS DELETAR:")
    plan_exists = InstallmentPlan.objects.filter(id=plan_id).exists()
    installments_exist = Installment.objects.filter(id__in=installment_ids).exists()
    transactions_exist = Transaction.objects.filter(id__in=transaction_ids).exists()
    
    print(f"   - Plano {plan_id} existe? {plan_exists}")
    print(f"   - Parcelas existem? {installments_exist}")
    print(f"   - Transações existem? {transactions_exist}")
    
    # 11. Estatísticas FINAIS
    stats_final = {
        'plans': InstallmentPlan.objects.count(),
        'installments': Installment.objects.count(),
        'transactions': Transaction.objects.count()
    }
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   - Planos: {stats_final['plans']} ({stats_final['plans'] - stats_after_create['plans']:+d})")
    print(f"   - Parcelas: {stats_final['installments']} ({stats_final['installments'] - stats_after_create['installments']:+d})")
    print(f"   - Transações: {stats_final['transactions']} ({stats_final['transactions'] - stats_after_create['transactions']:+d})")
    
    # 12. Validação
    print(f"\n✅ RESULTADOS:")
    success = True
    
    if plan_exists:
        print("   ❌ FALHA: Plano não foi deletado!")
        success = False
    else:
        print("   ✅ Plano deletado com sucesso")
    
    if installments_exist:
        print("   ❌ FALHA: Parcelas não foram deletadas!")
        success = False
    else:
        print("   ✅ Parcelas deletadas com sucesso")
    
    if transactions_exist:
        print("   ❌ FALHA: Transações não foram deletadas!")
        success = False
    else:
        print("   ✅ Transações deletadas com sucesso")
    
    # Verificar contadores
    expected_plans = stats_after_create['plans'] - 1
    expected_installments = stats_after_create['installments'] - 5
    expected_transactions = stats_after_create['transactions'] - 5
    
    if stats_final['plans'] == expected_plans:
        print(f"   ✅ Contagem de planos correta")
    else:
        print(f"   ❌ Contagem de planos incorreta (esperado: {expected_plans}, atual: {stats_final['plans']})")
        success = False
    
    if stats_final['installments'] == expected_installments:
        print(f"   ✅ Contagem de parcelas correta")
    else:
        print(f"   ❌ Contagem de parcelas incorreta (esperado: {expected_installments}, atual: {stats_final['installments']})")
        success = False
    
    if stats_final['transactions'] == expected_transactions:
        print(f"   ✅ Contagem de transações correta")
    else:
        print(f"   ❌ Contagem de transações incorreta (esperado: {expected_transactions}, atual: {stats_final['transactions']})")
        success = False
    
    print("\n" + "="*70)
    if success:
        print("✅ TESTE PASSOU! Deleção em cascata funcionando corretamente!")
    else:
        print("❌ TESTE FALHOU! Verifique os erros acima.")
    print("="*70 + "\n")
    
    return success


if __name__ == '__main__':
    try:
        success = test_cascade_delete()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

