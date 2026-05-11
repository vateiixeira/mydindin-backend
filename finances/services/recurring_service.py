"""
Serviço para gerenciar templates recorrentes e geração de transações
"""

import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from ..models import RecurringTemplate, Transaction


class RecurringService:
    """
    Serviço para lógica de negócio de templates recorrentes.
    """

    def _create_transaction_for_date(self, template, target_date):
        """Cria uma transação para uma data específica a partir de um template."""
        return Transaction.objects.create(
            user=template.user,
            category=template.category,
            type=template.type,
            description=template.description,
            amount=template.amount,
            payment_method=template.payment_method,
            credit_card=template.credit_card,
            transaction_date=target_date,
            due_date=target_date,
            status='pending',
            notes=f"Gerado automaticamente do template: {template.description}"
        )

    def generate_months(self, template, months, force=False):
        """
        Gera N transações mensais a partir do mês seguinte ao last_generated_date,
        ou do mês atual se nunca gerado.

        Args:
            template: Instância de RecurringTemplate
            months: Número de meses a gerar
            force: Se True, ignora verificação de end_date

        Returns:
            Tupla (lista de Transaction criadas, truncated) onde truncated indica
            se a geração foi interrompida por end_date.
        """
        today = date.today()

        if template.last_generated_date:
            # Começa do mês seguinte ao último gerado
            start = template.last_generated_date.replace(day=1) + relativedelta(months=1)
        else:
            # Começa do mês atual
            start = today.replace(day=1)

        transactions = []
        truncated = False
        for i in range(months):
            target_month = start + relativedelta(months=i)
            # Respeita o limite de dias do mês (ex: dia 31 em fevereiro → dia 28/29)
            last_day = calendar.monthrange(target_month.year, target_month.month)[1]
            day = min(template.day_of_month, last_day)
            target_date = date(target_month.year, target_month.month, day)

            if not force and template.end_date and target_date > template.end_date:
                truncated = True
                break

            transaction = self._create_transaction_for_date(template, target_date)
            transactions.append(transaction)

        if transactions:
            template.last_generated_date = transactions[-1].transaction_date
            template.save()

        return transactions, truncated

    def generate_all_from_start(self, template):
        """
        Gera todas as transações desde start_date até end_date (inclusive).
        Usado quando generate_now=True na criação do template.
        Requer que end_date esteja definido.
        """
        if not template.end_date:
            return []

        transactions = []
        current_month = template.start_date.replace(day=1)
        end_month = template.end_date.replace(day=1)

        while current_month <= end_month:
            last_day = calendar.monthrange(current_month.year, current_month.month)[1]
            day = min(template.day_of_month, last_day)
            target_date = date(current_month.year, current_month.month, day)

            if target_date >= template.start_date and target_date <= template.end_date:
                transaction = self._create_transaction_for_date(template, target_date)
                transactions.append(transaction)

            current_month = current_month + relativedelta(months=1)

        if transactions:
            template.last_generated_date = transactions[-1].transaction_date
            template.save()

        return transactions

    def generate_transaction_from_template(self, template):
        """
        Gera uma transação a partir de um template recorrente (para uso do Celery).
        Gera apenas 1 mês.

        Args:
            template: Instância de RecurringTemplate

        Returns:
            Transaction criada ou None se não foi possível criar
        """
        if not template.is_active:
            return None

        if template.end_date and date.today() > template.end_date:
            return None

        transactions, _ = self.generate_months(template, 1)
        return transactions[0] if transactions else None

    def should_generate_today(self, template):
        """
        Verifica se um template deve gerar transação hoje.
        """
        today = date.today()

        if not template.is_active:
            return False

        if template.end_date and today > template.end_date:
            return False

        if today < template.start_date:
            return False

        if today.day != template.day_of_month:
            return False

        if template.last_generated_date:
            if (template.last_generated_date.year == today.year and
                    template.last_generated_date.month == today.month):
                return False

        return True

    def process_all_templates(self):
        """
        Processa todos os templates ativos. Usado pelo Celery.
        """
        templates = RecurringTemplate.objects.filter(is_active=True)

        generated = 0
        skipped = 0
        errors = 0

        for template in templates:
            try:
                if self.should_generate_today(template):
                    transaction = self.generate_transaction_from_template(template)
                    if transaction:
                        generated += 1
                    else:
                        errors += 1
                else:
                    skipped += 1
            except Exception as e:
                errors += 1
                print(f"Erro ao processar template {template.id}: {str(e)}")

        return {
            'processed': templates.count(),
            'generated': generated,
            'skipped': skipped,
            'errors': errors
        }

    def get_next_generation_date(self, template):
        """
        Calcula a próxima data de geração para um template.
        """
        today = date.today()

        if today.day < template.day_of_month:
            return date(today.year, today.month, template.day_of_month)
        else:
            next_month = today + relativedelta(months=1)
            try:
                return date(next_month.year, next_month.month, template.day_of_month)
            except ValueError:
                next_month_last_day = (next_month + relativedelta(months=1, day=1)) - relativedelta(days=1)
                return next_month_last_day
