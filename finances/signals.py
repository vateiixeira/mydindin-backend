"""
Signals para automação de processos no app finances.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Transaction, Installment
from .services.invoice_service import InvoiceService


@receiver(post_save, sender=Transaction)
def auto_link_transaction_to_invoice(sender, instance, created, **kwargs):
    """
    Automaticamente vincula uma transação à fatura quando ela tem cartão de crédito.
    Cria a fatura automaticamente se não existir.
    """
    # Só processar se:
    # 1. É uma nova transação OU
    # 2. A transação foi atualizada e tem cartão mas não tem fatura vinculada
    if instance.credit_card and not instance.invoice:
        service = InvoiceService()
        
        try:
            invoice = service.link_transaction_to_invoice(instance)
            
            if invoice:
                # Atualizar total da fatura
                service.update_invoice_total(invoice)
                print(f"  ✓ Transação {instance.id} vinculada à fatura {invoice}")
        except Exception as e:
            print(f"  ✗ Erro ao vincular transação {instance.id} à fatura: {str(e)}")


@receiver(post_save, sender=Installment)
def auto_link_installment_to_invoice(sender, instance, created, **kwargs):
    """
    Automaticamente vincula uma parcela à fatura quando ela tem cartão de crédito.
    Cria a fatura automaticamente se não existir.
    """
    # Só processar se a parcela tem cartão de crédito mas não tem fatura vinculada
    if instance.plan.credit_card and not instance.invoice:
        service = InvoiceService()
        
        try:
            invoice = service.link_installment_to_invoice(instance)
            
            if invoice:
                # Atualizar total da fatura
                service.update_invoice_total(invoice)
                print(f"  ✓ Parcela {instance} vinculada à fatura {invoice}")
        except Exception as e:
            print(f"  ✗ Erro ao vincular parcela {instance} à fatura: {str(e)}")


@receiver(pre_delete, sender=Installment)
def delete_installment_transaction(sender, instance, **kwargs):
    """
    Automaticamente deleta a transação vinculada quando uma parcela é deletada.
    Isso garante que ao deletar um InstallmentPlan, todas as transações das parcelas
    também sejam deletadas.
    """
    try:
        if instance.transaction:
            transaction_id = instance.transaction.id
            instance.transaction.delete()
            print(f"  ✓ Transação {transaction_id} deletada junto com a parcela {instance.id}")
    except Transaction.DoesNotExist:
        # Transação já foi deletada ou não existe
        pass
    except Exception as e:
        print(f"  ✗ Erro ao deletar transação da parcela {instance.id}: {str(e)}")

