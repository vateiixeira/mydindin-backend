"""
Configuração do Celery para o projeto MyDinDin.
Define workers, beat scheduler e configurações de tasks.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Define o módulo de settings do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Cria a aplicação Celery
app = Celery('mydindin')

# Carrega as configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre automaticamente tasks em todos os apps instalados
app.autodiscover_tasks()

# Configuração do Celery Beat (tarefas periódicas)
app.conf.beat_schedule = {
    # Criar transações recorrentes diariamente às 00:01
    'create-recurring-transactions': {
        'task': 'finances.create_recurring_transactions',
        'schedule': crontab(hour=0, minute=1),  # 00:01 todo dia
        'options': {
            'expires': 3600,  # Expira em 1 hora se não executar
        }
    },
    
    # Criar transações de parcelas diariamente às 00:05
    'create-installment-transactions': {
        'task': 'finances.create_installment_transactions',
        'schedule': crontab(hour=0, minute=5),  # 00:05 todo dia
        'options': {
            'expires': 3600,
        }
    },
    
    # Atualizar status de atrasados diariamente às 00:10
    'update-overdue-status': {
        'task': 'finances.update_overdue_status',
        'schedule': crontab(hour=0, minute=10),  # 00:10 todo dia
        'options': {
            'expires': 3600,
        }
    },
    
    # Criar faturas de cartão de crédito diariamente às 00:15
    'create-credit-card-invoices': {
        'task': 'finances.create_credit_card_invoices',
        'schedule': crontab(hour=0, minute=15),  # 00:15 todo dia
        'options': {
            'expires': 3600,
        }
    },
    
    # Atualizar faturas atrasadas diariamente às 00:20
    'update-overdue-invoices': {
        'task': 'finances.update_overdue_invoices',
        'schedule': crontab(hour=0, minute=20),  # 00:20 todo dia
        'options': {
            'expires': 3600,
        }
    },
    
    # Limpeza opcional no primeiro dia do mês às 03:00
    'cleanup-old-data': {
        'task': 'finances.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # 03:00 no dia 1
        'options': {
            'expires': 7200,
        }
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task de debug para testar o Celery"""
    print(f'Request: {self.request!r}')

