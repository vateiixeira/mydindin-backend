"""
Tarefas Celery para o app finances.
Executa processamento assíncrono e periódico de transações.
"""

from celery import shared_task
from datetime import date
from django.utils import timezone
from .services.recurring_service import RecurringService
from .services.installment_service import InstallmentService
from .services.invoice_service import InvoiceService
from .models import Transaction


@shared_task(name='finances.create_recurring_transactions')
def create_recurring_transactions():
    """
    Task que processa todos os templates recorrentes e cria transações.
    Executada diariamente às 00:01 via Celery Beat.
    
    Returns:
        Dict com estatísticas de processamento
    """
    service = RecurringService()
    result = service.process_all_templates()
    
    # Log do resultado
    print(f"[RecurringTransactions] Processados: {result['processed']}, "
          f"Gerados: {result['generated']}, "
          f"Ignorados: {result['skipped']}, "
          f"Erros: {result['errors']}")
    
    return result


@shared_task(name='finances.create_installment_transactions')
def create_installment_transactions():
    """
    Task que processa todas as parcelas e cria transações quando necessário.
    Executada diariamente às 00:05 via Celery Beat.
    
    Returns:
        Dict com estatísticas de processamento
    """
    service = InstallmentService()
    result = service.process_all_installments()
    
    # Log do resultado
    print(f"[InstallmentTransactions] Processados: {result['processed']}, "
          f"Gerados: {result['generated']}, "
          f"Ignorados: {result['skipped']}, "
          f"Erros: {result['errors']}")
    
    return result


@shared_task(name='finances.update_overdue_status')
def update_overdue_status():
    """
    Task que atualiza o status de transações e parcelas atrasadas.
    Executada diariamente às 00:10 via Celery Beat.
    
    Returns:
        Dict com número de registros atualizados
    """
    today = date.today()
    
    # Atualizar transações atrasadas
    transactions_updated = Transaction.objects.filter(
        status='pending',
        due_date__lt=today,
        due_date__isnull=False
    ).update(status='overdue')
    
    # Atualizar parcelas atrasadas
    installment_service = InstallmentService()
    installments_updated = installment_service.update_overdue_installments()
    
    result = {
        'transactions_updated': transactions_updated,
        'installments_updated': installments_updated,
        'executed_at': timezone.now().isoformat()
    }
    
    # Log do resultado
    print(f"[UpdateOverdue] Transações: {transactions_updated}, "
          f"Parcelas: {installments_updated}")
    
    return result


@shared_task(name='finances.cleanup_old_data')
def cleanup_old_data():
    """
    Task opcional para limpeza de dados antigos.
    Pode ser configurada para rodar mensalmente.
    
    Por enquanto apenas registra execução, mas pode ser expandida para:
    - Arquivar transações muito antigas
    - Limpar logs
    - Etc.
    
    Returns:
        Dict com informações da execução
    """
    result = {
        'executed_at': timezone.now().isoformat(),
        'message': 'Cleanup task executada com sucesso'
    }
    
    print(f"[Cleanup] Executado em {result['executed_at']}")
    
    return result


# Tasks sob demanda (chamadas manualmente)

@shared_task(name='finances.generate_transaction_from_template')
def generate_transaction_from_template_task(template_id):
    """
    Task para gerar uma transação manualmente de um template.
    
    Args:
        template_id: ID do RecurringTemplate
        
    Returns:
        Dict com resultado da operação
    """
    from .models import RecurringTemplate
    
    try:
        template = RecurringTemplate.objects.get(id=template_id)
        service = RecurringService()
        transaction = service.generate_transaction_from_template(template)
        
        if transaction:
            return {
                'success': True,
                'transaction_id': transaction.id,
                'message': f'Transação {transaction.id} criada com sucesso'
            }
        else:
            return {
                'success': False,
                'message': 'Não foi possível criar a transação'
            }
    except RecurringTemplate.DoesNotExist:
        return {
            'success': False,
            'message': f'Template {template_id} não encontrado'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro: {str(e)}'
        }


@shared_task(name='finances.generate_transaction_from_installment')
def generate_transaction_from_installment_task(installment_id):
    """
    Task para gerar uma transação manualmente de uma parcela.
    
    Args:
        installment_id: ID da Installment
        
    Returns:
        Dict com resultado da operação
    """
    from .models import Installment
    
    try:
        installment = Installment.objects.get(id=installment_id)
        service = InstallmentService()
        transaction = service.generate_transaction_from_installment(installment)
        
        if transaction:
            return {
                'success': True,
                'transaction_id': transaction.id,
                'message': f'Transação {transaction.id} criada com sucesso'
            }
        else:
            return {
                'success': False,
                'message': 'Não foi possível criar a transação (pode já existir)'
            }
    except Installment.DoesNotExist:
        return {
            'success': False,
            'message': f'Parcela {installment_id} não encontrada'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro: {str(e)}'
        }


# ========== TASKS PARA FATURAS DE CARTÃO DE CRÉDITO ==========

@shared_task(name='finances.create_credit_card_invoices')
def create_credit_card_invoices():
    """
    Task que cria faturas de cartão de crédito automaticamente.
    Executada diariamente às 00:15 via Celery Beat.
    
    Cria faturas quando a data de fechamento já passou.
    Garante que só existe 1 fatura por reference_month.
    
    Returns:
        Dict com estatísticas de processamento
    """
    service = InvoiceService()
    result = service.create_pending_invoices()
    
    # Log do resultado
    print(f"[CreditCardInvoices] Processados: {result['processed']}, "
          f"Criados: {result['created']}, "
          f"Ignorados: {result['skipped']}, "
          f"Erros: {len(result['errors'])}")
    
    if result['errors']:
        for error in result['errors']:
            print(f"  ✗ {error}")
    
    return result


@shared_task(name='finances.update_overdue_invoices')
def update_overdue_invoices():
    """
    Task que atualiza o status de faturas atrasadas.
    Executada diariamente às 00:20 via Celery Beat.
    
    Returns:
        Dict com número de faturas atualizadas
    """
    service = InvoiceService()
    updated = service.update_overdue_invoices()
    
    result = {
        'invoices_updated': updated,
        'executed_at': timezone.now().isoformat()
    }
    
    # Log do resultado
    print(f"[UpdateOverdueInvoices] Faturas atualizadas: {updated}")
    
    return result


@shared_task(name='finances.link_transaction_to_invoice')
def link_transaction_to_invoice_task(transaction_id):
    """
    Task assíncrona para vincular uma transação à fatura correta.
    Cria a fatura automaticamente se não existir.
    
    Args:
        transaction_id: ID da Transaction
        
    Returns:
        Dict com resultado da operação
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if not transaction.credit_card:
            return {
                'success': False,
                'message': 'Transação não tem cartão de crédito vinculado'
            }
        
        service = InvoiceService()
        invoice = service.link_transaction_to_invoice(transaction)
        
        if invoice:
            # Atualizar total da fatura
            service.update_invoice_total(invoice)
            
            return {
                'success': True,
                'invoice_id': invoice.id,
                'message': f'Transação vinculada à fatura {invoice}'
            }
        else:
            return {
                'success': False,
                'message': 'Não foi possível vincular à fatura'
            }
    except Transaction.DoesNotExist:
        return {
            'success': False,
            'message': f'Transação {transaction_id} não encontrada'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro: {str(e)}'
        }

