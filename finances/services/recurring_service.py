"""
Serviço para gerenciar templates recorrentes e geração de transações
"""

from datetime import date
from django.utils import timezone
from ..models import RecurringTemplate, Transaction


class RecurringService:
    """
    Serviço para lógica de negócio de templates recorrentes.
    Responsável por gerar transações automaticamente baseado nos templates.
    """
    
    def generate_transaction_from_template(self, template):
        """
        Gera uma transação a partir de um template recorrente.
        
        Args:
            template: Instância de RecurringTemplate
            
        Returns:
            Transaction criada ou None se não foi possível criar
        """
        # Validações
        if not template.is_active:
            return None
        
        # Verificar se já passou da data de término
        if template.end_date and date.today() > template.end_date:
            return None
        
        # Criar a transação
        transaction = Transaction.objects.create(
            user=template.user,
            category=template.category,
            type=template.type,
            description=template.description,
            amount=template.amount,
            transaction_date=date.today(),
            due_date=date.today(),
            status='pending',
            notes=f"Gerado automaticamente do template: {template.description}"
        )
        
        # Atualizar última geração
        template.last_generated_date = date.today()
        template.save()
        
        return transaction
    
    def should_generate_today(self, template):
        """
        Verifica se um template deve gerar transação hoje.
        
        Args:
            template: Instância de RecurringTemplate
            
        Returns:
            Boolean indicando se deve gerar
        """
        today = date.today()
        
        # Verificar se está ativo
        if not template.is_active:
            return False
        
        # Verificar se já passou da data de término
        if template.end_date and today > template.end_date:
            return False
        
        # Verificar se ainda não começou
        if today < template.start_date:
            return False
        
        # Verificar se hoje é o dia do mês configurado
        if today.day != template.day_of_month:
            return False
        
        # Verificar se já foi gerado este mês
        if template.last_generated_date:
            if (template.last_generated_date.year == today.year and 
                template.last_generated_date.month == today.month):
                return False
        
        return True
    
    def process_all_templates(self):
        """
        Processa todos os templates ativos e gera transações quando necessário.
        Usado pelo Celery para execução diária.
        
        Returns:
            Dict com estatísticas de processamento
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
        
        Args:
            template: Instância de RecurringTemplate
            
        Returns:
            Date da próxima geração ou None
        """
        from dateutil.relativedelta import relativedelta
        
        today = date.today()
        
        # Se hoje é antes do dia configurado no mês atual
        if today.day < template.day_of_month:
            return date(today.year, today.month, template.day_of_month)
        else:
            # Próximo mês
            next_month = today + relativedelta(months=1)
            try:
                return date(next_month.year, next_month.month, template.day_of_month)
            except ValueError:
                # Caso o dia não exista no próximo mês (ex: 31 de fevereiro)
                # Usa o último dia do mês
                next_month_last_day = (next_month + relativedelta(months=1, day=1)) - relativedelta(days=1)
                return next_month_last_day

