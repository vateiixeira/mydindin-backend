"""
Serviço para gerenciar planos de parcelamento e suas parcelas
"""

from datetime import date, timedelta
from django.db import transaction as db_transaction
from ..models import InstallmentPlan, Installment, Transaction


class InstallmentService:
    """
    Serviço para lógica de negócio de planos de parcelamento.
    Responsável por criar transações das parcelas.
    """
    
    def __init__(self, days_before_due=7):
        """
        Args:
            days_before_due: Quantos dias antes do vencimento criar a transação
        """
        self.days_before_due = days_before_due
    
    def generate_transaction_from_installment(self, installment):
        """
        Gera uma transação a partir de uma parcela.
        
        Args:
            installment: Instância de Installment
            
        Returns:
            Transaction criada ou None se não foi possível criar
        """
        # Validações
        if installment.transaction:
            # Já existe uma transação para esta parcela
            return None
        
        if installment.status not in ['pending', 'overdue']:
            # Só gera para parcelas pendentes ou atrasadas
            return None
        
        # Criar a transação
        transaction = Transaction.objects.create(
            user=installment.plan.user,
            category=installment.plan.category,
            type=installment.plan.type,
            description=f"{installment.plan.description} - Parcela {installment.installment_number}/{installment.plan.total_installments}",
            amount=installment.amount,
            credit_card=installment.plan.credit_card,  # Vincula ao cartão se houver
            transaction_date=date.today(),
            due_date=installment.due_date,
            status='pending',
            notes=f"Gerado automaticamente da parcela {installment.id}"
        )
        
        # Vincular a transação à parcela
        installment.transaction = transaction
        installment.status = 'generated'
        installment.save()
        
        return transaction
    
    def should_generate_transaction(self, installment):
        """
        Verifica se uma parcela deve ter sua transação gerada.
        
        Args:
            installment: Instância de Installment
            
        Returns:
            Boolean indicando se deve gerar
        """
        # Já tem transação
        if installment.transaction:
            return False
        
        # Já está paga
        if installment.status == 'paid':
            return False
        
        # Plano não está ativo
        if not installment.plan.is_active:
            return False
        
        # Verifica se está dentro do período de geração
        today = date.today()
        generation_date = installment.due_date - timedelta(days=self.days_before_due)
        
        # Gera se hoje >= data de geração ou se já está atrasada
        return today >= generation_date or installment.status == 'overdue'
    
    def process_all_installments(self):
        """
        Processa todas as parcelas e gera transações quando necessário.
        Usado pelo Celery para execução diária.
        
        Returns:
            Dict com estatísticas de processamento
        """
        # Busca parcelas que precisam de transação
        installments = Installment.objects.filter(
            plan__is_active=True,
            status__in=['pending', 'overdue'],
            transaction__isnull=True
        ).select_related('plan', 'plan__user', 'plan__category')
        
        generated = 0
        skipped = 0
        errors = 0
        
        for installment in installments:
            try:
                if self.should_generate_transaction(installment):
                    transaction = self.generate_transaction_from_installment(installment)
                    if transaction:
                        generated += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            except Exception as e:
                errors += 1
                print(f"Erro ao processar parcela {installment.id}: {str(e)}")
        
        return {
            'processed': installments.count(),
            'generated': generated,
            'skipped': skipped,
            'errors': errors
        }
    
    def update_overdue_installments(self):
        """
        Atualiza o status de parcelas atrasadas.
        Marca como 'overdue' parcelas pendentes com vencimento passado.
        
        Returns:
            Número de parcelas atualizadas
        """
        today = date.today()
        
        updated = Installment.objects.filter(
            status='pending',
            due_date__lt=today
        ).update(status='overdue')
        
        return updated
    
    def mark_installment_as_paid(self, installment):
        """
        Marca uma parcela como paga e sua transação também.
        
        Args:
            installment: Instância de Installment
            
        Returns:
            Boolean indicando sucesso
        """
        with db_transaction.atomic():
            # Marca a parcela como paga
            installment.status = 'paid'
            installment.save()
            
            # Se existe transação vinculada, marca ela como paga também
            if installment.transaction:
                installment.transaction.status = 'paid'
                installment.transaction.payment_date = date.today()
                installment.transaction.save()
            
            return True
    
    def get_upcoming_installments(self, user, days=30):
        """
        Retorna parcelas que vencem nos próximos X dias.
        
        Args:
            user: Usuário
            days: Número de dias à frente
            
        Returns:
            QuerySet de Installment
        """
        today = date.today()
        future_date = today + timedelta(days=days)
        
        return Installment.objects.filter(
            plan__user=user,
            plan__is_active=True,
            status__in=['pending', 'generated'],
            due_date__gte=today,
            due_date__lte=future_date
        ).select_related('plan').order_by('due_date')
    
    def get_plan_summary(self, plan):
        """
        Retorna um resumo completo do plano.
        
        Args:
            plan: Instância de InstallmentPlan
            
        Returns:
            Dict com informações do plano
        """
        installments = plan.installments.all()
        
        total = installments.count()
        pending = installments.filter(status='pending').count()
        paid = installments.filter(status='paid').count()
        overdue = installments.filter(status='overdue').count()
        generated = installments.filter(status='generated').count()
        
        total_amount = sum([inst.amount for inst in installments])
        paid_amount = sum([inst.amount for inst in installments.filter(status='paid')])
        
        return {
            'plan': plan,
            'total_installments': total,
            'pending_installments': pending,
            'paid_installments': paid,
            'overdue_installments': overdue,
            'generated_installments': generated,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'remaining_amount': total_amount - paid_amount,
            'progress_percentage': (paid / total * 100) if total > 0 else 0
        }

