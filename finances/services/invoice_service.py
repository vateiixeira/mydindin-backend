"""
Serviço para gerenciamento automático de faturas de cartão de crédito.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db.models import Q
from ..models import CreditCard, CreditCardInvoice, Transaction, Installment


class InvoiceService:
    """
    Serviço responsável por criar e gerenciar faturas de cartão de crédito automaticamente.
    """
    
    @staticmethod
    def get_invoice_month_for_transaction(credit_card, transaction_date):
        """
        Determina qual mês de referência da fatura uma transação pertence.
        
        Args:
            credit_card: Objeto CreditCard
            transaction_date: Data da transação (date)
            
        Returns:
            date: Primeiro dia do mês de referência da fatura
        """
        closing_day = credit_card.closing_day
        
        # Se a transação ocorreu antes do dia de fechamento, pertence à fatura do mês atual
        if transaction_date.day <= closing_day:
            reference_month = date(transaction_date.year, transaction_date.month, 1)
        else:
            # Se foi após o fechamento, pertence à fatura do mês seguinte
            reference_month = date(transaction_date.year, transaction_date.month, 1) + relativedelta(months=1)
        
        return reference_month
    
    @staticmethod
    def calculate_invoice_dates(credit_card, reference_month):
        """
        Calcula as datas de fechamento e vencimento de uma fatura.
        
        Args:
            credit_card: Objeto CreditCard
            reference_month: Primeiro dia do mês de referência (date)
            
        Returns:
            tuple: (closing_date, due_date)
        """
        closing_day = credit_card.closing_day
        due_day = credit_card.due_day
        
        # Data de fechamento é no dia de fechamento do mês de referência
        try:
            closing_date = date(reference_month.year, reference_month.month, closing_day)
        except ValueError:
            # Se o mês não tem o dia especificado (ex: 31 em fevereiro), usa último dia do mês
            closing_date = reference_month + relativedelta(months=1, days=-1)
        
        # Data de vencimento é no mês seguinte ao de referência
        next_month = reference_month + relativedelta(months=1)
        try:
            due_date = date(next_month.year, next_month.month, due_day)
        except ValueError:
            # Se o mês não tem o dia especificado, usa último dia do mês
            due_date = next_month + relativedelta(months=1, days=-1)
        
        return closing_date, due_date
    
    @staticmethod
    def get_or_create_invoice(credit_card, reference_month):
        """
        Obtém ou cria uma fatura para o cartão e mês de referência.
        
        Args:
            credit_card: Objeto CreditCard
            reference_month: Primeiro dia do mês de referência (date)
            
        Returns:
            tuple: (invoice, created) onde created é True se foi criada nova fatura
        """
        # Garantir que reference_month é o primeiro dia do mês
        reference_month = date(reference_month.year, reference_month.month, 1)
        
        # Verificar se já existe fatura para este mês
        invoice = CreditCardInvoice.objects.filter(
            credit_card=credit_card,
            reference_month=reference_month
        ).first()
        
        if invoice:
            return invoice, False
        
        # Criar nova fatura
        closing_date, due_date = InvoiceService.calculate_invoice_dates(credit_card, reference_month)
        
        invoice = CreditCardInvoice.objects.create(
            credit_card=credit_card,
            reference_month=reference_month,
            total_amount=Decimal('0.00'),  # Será atualizado posteriormente
            closing_date=closing_date,
            due_date=due_date,
            status='pending'
        )
        
        return invoice, True
    
    @staticmethod
    def create_pending_invoices():
        """
        Cria faturas pendentes para todos os cartões ativos.
        Cria faturas quando a data de fechamento já passou.
        Também vincula parcelas (installments) pendentes que ainda não têm fatura.
        
        Returns:
            dict: Estatísticas de processamento
        """
        from ..models import Installment
        
        today = date.today()
        stats = {
            'processed': 0,
            'created': 0,
            'skipped': 0,
            'linked_installments': 0,
            'errors': []
        }
        
        # Buscar todos os cartões ativos
        active_cards = CreditCard.objects.filter(is_active=True)
        
        for card in active_cards:
            stats['processed'] += 1
            
            try:
                # Verificar se precisa criar fatura para o mês atual
                current_month = date(today.year, today.month, 1)
                
                # Calcular data de fechamento do mês atual
                closing_date, _ = InvoiceService.calculate_invoice_dates(card, current_month)
                
                # Se a data de fechamento já passou, criar fatura se não existir
                if today >= closing_date:
                    invoice, created = InvoiceService.get_or_create_invoice(card, current_month)
                    
                    if created:
                        stats['created'] += 1
                        print(f"  ✓ Fatura criada: {card.name} - {current_month.strftime('%m/%Y')}")
                    else:
                        stats['skipped'] += 1
                
                # Também verificar o mês seguinte (para criar com antecedência se desejado)
                # Descomentado: Criar fatura do próximo mês assim que o mês atual fechar
                next_month = current_month + relativedelta(months=1)
                next_closing_date, _ = InvoiceService.calculate_invoice_dates(card, next_month)
                
                # Se já passamos do fechamento do mês atual, podemos criar a do próximo
                if today >= closing_date:
                    invoice, created = InvoiceService.get_or_create_invoice(card, next_month)
                    if created:
                        stats['created'] += 1
                        print(f"  ✓ Fatura criada (próximo mês): {card.name} - {next_month.strftime('%m/%Y')}")
                
            except Exception as e:
                error_msg = f"Erro ao processar cartão {card.name}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        # Processar parcelas (installments) pendentes que ainda não têm fatura vinculada
        print("\n  ⏳ Processando parcelas pendentes...")
        
        for card in active_cards:
            try:
                # Buscar parcelas deste cartão que ainda não têm fatura
                pending_installments = Installment.objects.filter(
                    plan__credit_card=card,
                    plan__is_active=True,
                    invoice__isnull=True,
                    status__in=['pending', 'generated', 'overdue']
                ).select_related('plan')
                
                for installment in pending_installments:
                    try:
                        # Vincular parcela à fatura apropriada
                        invoice = InvoiceService.link_installment_to_invoice(installment)
                        
                        if invoice:
                            stats['linked_installments'] += 1
                            
                            # Atualizar total da fatura
                            InvoiceService.update_invoice_total(invoice)
                            
                    except Exception as e:
                        error_msg = f"Erro ao vincular parcela {installment.id}: {str(e)}"
                        stats['errors'].append(error_msg)
                        print(f"  ✗ {error_msg}")
                        
            except Exception as e:
                error_msg = f"Erro ao processar parcelas do cartão {card.name}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        if stats['linked_installments'] > 0:
            print(f"  ✓ {stats['linked_installments']} parcelas vinculadas a faturas")
        
        return stats
    
    @staticmethod
    def link_transaction_to_invoice(transaction):
        """
        Vincula uma transação à fatura correta do cartão de crédito.
        Cria a fatura automaticamente se não existir.
        
        Args:
            transaction: Objeto Transaction com credit_card definido
            
        Returns:
            CreditCardInvoice ou None
        """
        if not transaction.credit_card:
            return None
        
        # Determinar o mês de referência da fatura
        reference_month = InvoiceService.get_invoice_month_for_transaction(
            transaction.credit_card,
            transaction.transaction_date
        )
        
        # Obter ou criar a fatura
        invoice, created = InvoiceService.get_or_create_invoice(
            transaction.credit_card,
            reference_month
        )
        
        # Vincular a transação à fatura
        transaction.invoice = invoice
        transaction.save(update_fields=['invoice'])
        
        if created:
            print(f"  ✓ Fatura criada automaticamente: {invoice}")
        
        return invoice
    
    @staticmethod
    def link_installment_to_invoice(installment):
        """
        Vincula uma parcela à fatura correta do cartão de crédito.
        Cria a fatura automaticamente se não existir.
        Também vincula a transação da parcela (se existir) à mesma fatura.
        
        Args:
            installment: Objeto Installment com plan.credit_card definido
            
        Returns:
            CreditCardInvoice ou None
        """
        if not installment.plan.credit_card:
            return None
        
        # Determinar o mês de referência da fatura baseado na due_date da parcela
        reference_month = InvoiceService.get_invoice_month_for_transaction(
            installment.plan.credit_card,
            installment.due_date
        )
        
        # Obter ou criar a fatura
        invoice, created = InvoiceService.get_or_create_invoice(
            installment.plan.credit_card,
            reference_month
        )
        
        # Vincular a parcela à fatura
        installment.invoice = invoice
        installment.save(update_fields=['invoice'])
        print(f"  ✓ Parcela {installment.id} vinculada à fatura {invoice}")
        
        # Se a parcela tem uma transação vinculada, vincular também à fatura
        try:
            if installment.transaction and not installment.transaction.invoice:
                installment.transaction.invoice = invoice
                installment.transaction.save(update_fields=['invoice'])
                print(f"  ✓ Transação {installment.transaction.id} da parcela vinculada à fatura {invoice}")
        except Exception as e:
            print(f"  ⚠ Erro ao vincular transação da parcela: {str(e)}")
        
        if created:
            print(f"  ✓ Fatura criada automaticamente para parcela: {invoice}")
        
        return invoice
    
    @staticmethod
    def update_invoice_total(invoice):
        """
        Atualiza o valor total da fatura baseado nas transações e parcelas vinculadas.
        
        Args:
            invoice: Objeto CreditCardInvoice
        """
        total_declared = invoice.get_declared_expenses()
        
        # Só atualiza se o total declarado for maior que o total atual
        # (isso preserva valores manuais inseridos pelo usuário)
        if total_declared > invoice.total_amount:
            invoice.total_amount = total_declared
            invoice.save(update_fields=['total_amount'])
    
    @staticmethod
    def update_overdue_invoices():
        """
        Atualiza o status de faturas atrasadas.
        
        Returns:
            int: Número de faturas atualizadas
        """
        today = date.today()
        
        updated = CreditCardInvoice.objects.filter(
            status='pending',
            due_date__lt=today
        ).update(status='overdue')
        
        return updated

