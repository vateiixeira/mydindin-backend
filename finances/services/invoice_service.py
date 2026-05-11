"""
Serviço para gerenciamento automático de faturas de cartão de crédito.
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
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
    
    # Lookback máximo para evitar loops longos em cartões sem histórico (3 anos)
    MAX_LOOKBACK_MONTHS = 36

    @staticmethod
    def _get_card_start_month(card):
        """
        Determina o mês de início mais antigo relevante para o cartão:
        mês da fatura mais antiga, da transação mais antiga vinculada, ou do created_at do cartão.
        Limitado a MAX_LOOKBACK_MONTHS meses atrás para evitar iterações excessivas.
        """
        today = date.today()
        floor_month = date(today.year, today.month, 1) - relativedelta(months=InvoiceService.MAX_LOOKBACK_MONTHS)

        card_created_date = timezone.localtime(card.created_at).date()
        candidates = [date(card_created_date.year, card_created_date.month, 1)]

        oldest_invoice = CreditCardInvoice.objects.filter(
            credit_card=card
        ).order_by('reference_month').values_list('reference_month', flat=True).first()
        if oldest_invoice:
            candidates.append(date(oldest_invoice.year, oldest_invoice.month, 1))

        oldest_txn_date = Transaction.objects.filter(
            credit_card=card
        ).order_by('transaction_date').values_list('transaction_date', flat=True).first()
        if oldest_txn_date:
            candidates.append(date(oldest_txn_date.year, oldest_txn_date.month, 1))

        return max(min(candidates), floor_month)

    @staticmethod
    def _should_create_month_invoice(card, reference_month, today=None):
        """
        Retorna True se a fatura do mês deve ser criada:
        - closing_date já passou, OU
        - hoje está a ≤ 10 dias do due_date
        """
        if today is None:
            today = date.today()

        closing_date, due_date = InvoiceService.calculate_invoice_dates(card, reference_month)

        if today >= closing_date:
            return True

        # Se closing_date ainda não passou, verifica proximidade do due_date.
        # Para due_date no passado timedelta.days seria negativo (≤ 10), mas closing_date < due_date
        # e today >= closing_date já teria retornado True — esta condição cobre apenas datas futuras.
        if (due_date - today).days <= 10:
            return True

        return False

    @staticmethod
    def generate_invoices_for_card(card, up_to_month=None):
        """
        Gera todas as faturas faltantes para o cartão desde o mês mais antigo relevante
        até up_to_month (padrão: mês atual).

        Só cria fatura do mês atual se closing_date já passou ou hoje está a ≤ 10 dias do due_date.

        Returns:
            dict: { 'created': int, 'skipped': int, 'months': list[str] }
        """
        today = date.today()
        current_month = date(today.year, today.month, 1)

        if up_to_month is None:
            up_to_month = current_month

        # Nunca gerar faturas de meses futuros
        up_to_month = min(up_to_month, current_month)

        start_month = InvoiceService._get_card_start_month(card)

        created = 0
        skipped = 0
        months = []

        month = start_month
        while month <= up_to_month:
            if month == current_month:
                if not InvoiceService._should_create_month_invoice(card, month, today):
                    break

            invoice, was_created = InvoiceService.get_or_create_invoice(card, month)
            months.append(month.strftime('%m/%Y'))

            if was_created:
                created += 1
            else:
                skipped += 1

            month = month + relativedelta(months=1)

        return {'created': created, 'skipped': skipped, 'months': months}

    @staticmethod
    def create_pending_invoices():
        """
        Cria faturas pendentes para todos os cartões ativos.
        Itera desde o mês mais antigo relevante até o mês atual, criando faturas faltantes.
        Também vincula parcelas (installments) pendentes que ainda não têm fatura.

        Returns:
            dict: Estatísticas de processamento
        """
        from ..models import Installment

        stats = {
            'processed': 0,
            'created': 0,
            'skipped': 0,
            'linked_installments': 0,
            'errors': []
        }

        active_cards = CreditCard.objects.filter(is_active=True)

        for card in active_cards:
            stats['processed'] += 1

            try:
                result = InvoiceService.generate_invoices_for_card(card)
                stats['created'] += result['created']
                stats['skipped'] += result['skipped']

                for month_str in result['months']:
                    print(f"  ✓ Fatura processada: {card.name} - {month_str}")

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

