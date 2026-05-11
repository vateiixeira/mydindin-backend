from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum

User = get_user_model()


class Category(models.Model):
    """
    Modelo para categorias de transações financeiras.
    Pode ser usado tanto para receitas quanto para despesas.
    """
    
    TYPE_CHOICES = [
        ('income', 'Receita'),
        ('expense', 'Despesa'),
    ]
    
    name = models.CharField('Nome', max_length=100)
    type = models.CharField('Tipo', max_length=10, choices=TYPE_CHOICES)
    description = models.TextField('Descrição', blank=True, null=True)
    is_default = models.BooleanField('Categoria Padrão', default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='Usuário',
        null=True,
        blank=True,
        help_text='Deixe em branco para categorias padrão do sistema'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['type', 'name']
        unique_together = [['name', 'type', 'user']]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class Transaction(models.Model):
    """
    Modelo para transações financeiras (receitas e despesas).
    Suporta recorrência mensal e data máxima de pagamento.
    """
    
    TYPE_CHOICES = [
        ('income', 'Receita'),
        ('expense', 'Despesa'),
    ]
    
    RECURRENCE_CHOICES = [
        ('none', 'Não recorrente'),
        ('monthly', 'Mensal'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('overdue', 'Atrasado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('credito', 'Crédito'),
        ('debito', 'Débito'),
        ('dinheiro', 'Dinheiro'),
        ('transferencia', 'Transferência'),
        ('dda', 'DDA'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Usuário'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='Categoria'
    )
    type = models.CharField('Tipo', max_length=10, choices=TYPE_CHOICES)
    description = models.CharField('Descrição', max_length=255)
    amount = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Cartão de crédito (opcional)
    credit_card = models.ForeignKey(
        'CreditCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Cartão de Crédito',
        help_text='Vincula esta transação a um cartão de crédito'
    )
    invoice = models.ForeignKey(
        'CreditCardInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Fatura',
        help_text='Vincula esta transação a uma fatura específica'
    )
    
    # Campos de data
    transaction_date = models.DateField('Data da Transação')
    due_date = models.DateField(
        'Data de Vencimento',
        null=True,
        blank=True,
        help_text='Data máxima para pagamento (útil para condomínio, contas, etc)'
    )
    payment_date = models.DateField(
        'Data do Pagamento',
        null=True,
        blank=True
    )
    
    # Recorrência
    is_recurring = models.BooleanField('É Recorrente', default=False)
    recurrence = models.CharField(
        'Recorrência',
        max_length=10,
        choices=RECURRENCE_CHOICES,
        default='none'
    )
    recurrence_end_date = models.DateField(
        'Data Final da Recorrência',
        null=True,
        blank=True,
        help_text='Deixe em branco para recorrência sem fim'
    )
    
    # Status
    status = models.CharField(
        'Status',
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Observações
    notes = models.TextField('Observações', blank=True, null=True)

    # Forma de pagamento (opcional)
    payment_method = models.CharField(
        'Forma de Pagamento',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True
    )

    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['user', 'type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.description} - R$ {self.amount}"
    
    def save(self, *args, **kwargs):
        # Garantir que o tipo da categoria corresponde ao tipo da transação
        if self.category and self.category.type != self.type:
            raise ValueError('O tipo da categoria deve corresponder ao tipo da transação')
        
        # Atualizar recorrência baseado no campo is_recurring
        if not self.is_recurring:
            self.recurrence = 'none'
        elif self.is_recurring and self.recurrence == 'none':
            self.recurrence = 'monthly'

        # Atualizar status da parcela vinculada (se existir)
        try:
            if self.installment:
                self.installment.status = self.status
                self.installment.save()
        except Installment.DoesNotExist:
            # Transação não está vinculada a nenhuma parcela
            pass
        
        super().save(*args, **kwargs)


class RecurringTemplate(models.Model):
    """
    Modelo para templates de transações recorrentes.
    Usado para salários, aluguéis, assinaturas, etc.
    O Celery usa este modelo para criar transações automaticamente.
    """
    
    TYPE_CHOICES = [
        ('income', 'Receita'),
        ('expense', 'Despesa'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('credito', 'Crédito'),
        ('debito', 'Débito'),
        ('dinheiro', 'Dinheiro'),
        ('transferencia', 'Transferência'),
        ('dda', 'DDA'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recurring_templates',
        verbose_name='Usuário'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='recurring_templates',
        verbose_name='Categoria'
    )
    type = models.CharField('Tipo', max_length=10, choices=TYPE_CHOICES)
    description = models.CharField('Descrição', max_length=255)
    amount = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    day_of_month = models.PositiveIntegerField(
        'Dia do Mês',
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês para criar a transação (1-31)'
    )
    is_active = models.BooleanField('Ativo', default=True)
    start_date = models.DateField(
        'Data de Início',
        help_text='Quando começou este template'
    )
    end_date = models.DateField(
        'Data de Término',
        null=True,
        blank=True,
        help_text='Deixe em branco para recorrência sem fim'
    )
    last_generated_date = models.DateField(
        'Última Geração',
        null=True,
        blank=True,
        help_text='Última vez que uma transação foi gerada'
    )
    notes = models.TextField('Observações', blank=True, null=True)

    # Forma de pagamento (opcional)
    payment_method = models.CharField(
        'Forma de Pagamento',
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True
    )

    # Cartão de crédito (opcional, para templates com pagamento via crédito)
    credit_card = models.ForeignKey(
        'CreditCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_templates',
        verbose_name='Cartão de Crédito',
        help_text='Vincula este template a um cartão de crédito'
    )

    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Template Recorrente'
        verbose_name_plural = 'Templates Recorrentes'
        ordering = ['-is_active', 'day_of_month', 'description']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['day_of_month']),
        ]
    
    def __str__(self):
        return f"{self.description} - Dia {self.day_of_month} - R$ {self.amount}"
    
    def clean(self):
        # Validar que a categoria e o template são do mesmo tipo
        if self.category and self.category.type != self.type:
            raise ValidationError('O tipo da categoria deve corresponder ao tipo do template')
        
        # Validar que end_date é maior que start_date
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError('A data de término deve ser posterior à data de início')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class InstallmentPlan(models.Model):
    """
    Modelo para planos de parcelamento.
    Usado para consórcios, financiamentos, pagamentos parcelados, etc.
    """
    
    TYPE_CHOICES = [
        ('income', 'Receita'),
        ('expense', 'Despesa'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='installment_plans',
        verbose_name='Usuário'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='installment_plans',
        verbose_name='Categoria'
    )
    type = models.CharField('Tipo', max_length=10, choices=TYPE_CHOICES)
    description = models.CharField('Descrição', max_length=255)
    
    # Cartão de crédito (opcional)
    credit_card = models.ForeignKey(
        'CreditCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installment_plans',
        verbose_name='Cartão de Crédito',
        help_text='Vincula este parcelamento a um cartão de crédito'
    )
    total_installments = models.PositiveIntegerField(
        'Total de Parcelas',
        validators=[MinValueValidator(1)]
    )
    default_amount = models.DecimalField(
        'Valor Padrão das Parcelas',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Valor base de cada parcela (pode ser alterado individualmente)'
    )
    start_date = models.DateField(
        'Data da Primeira Parcela',
        help_text='Vencimento da primeira parcela'
    )
    is_active = models.BooleanField('Ativo', default=True)
    notes = models.TextField('Observações', blank=True, null=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Plano de Parcelamento'
        verbose_name_plural = 'Planos de Parcelamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.total_installments}x de R$ {self.default_amount}"
    
    def clean(self):
        # Validar que a categoria e o plano são do mesmo tipo
        if self.category and self.category.type != self.type:
            raise ValidationError('O tipo da categoria deve corresponder ao tipo do plano')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Criar parcelas automaticamente se for novo plano
        if is_new:
            self._create_installments()
    
    def _create_installments(self):
        """Cria todas as parcelas do plano e suas transações correspondentes"""
        from django.db import transaction as db_transaction
        from finances.services.invoice_service import InvoiceService
        
        current_date = self.start_date
        
        # Usar transação atômica para garantir consistência
        with db_transaction.atomic():
            # Criar cada parcela individualmente para disparar signals
            for i in range(1, self.total_installments + 1):
                # Criar parcela individualmente (dispara signal post_save)
                installment = Installment.objects.create(
                    plan=self,
                    installment_number=i,
                    amount=self.default_amount,
                    due_date=current_date,
                    status='pending'
                )
                
                # Criar transação individualmente (dispara signal post_save)
                transaction_obj = Transaction.objects.create(
                    user=self.user,
                    category=self.category,
                    type=self.type,
                    description=f"{self.description} - Parcela {installment.installment_number}/{self.total_installments}",
                    amount=installment.amount,
                    credit_card=self.credit_card,  # Vincula ao cartão se houver
                    transaction_date=installment.due_date,  # Data da transação = vencimento da parcela
                    due_date=installment.due_date,
                    status='pending',
                    notes=f"Gerado automaticamente do parcelamento {self.description}"
                )
                
                # Vincular transação à parcela
                installment.transaction = transaction_obj
                installment.status = 'generated'
                installment.save()  # Salva individualmente para disparar signals
                
                # Adiciona 1 mês para a próxima parcela
                current_date = current_date + relativedelta(months=1)


class Installment(models.Model):
    """
    Modelo para parcelas individuais de um plano.
    Cada parcela pode ter valor e vencimento customizados.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('generated', 'Transação Gerada'),
        ('paid', 'Pago'),
        ('overdue', 'Atrasado'),
    ]
    
    plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.CASCADE,
        related_name='installments',
        verbose_name='Plano'
    )
    installment_number = models.PositiveIntegerField(
        'Número da Parcela',
        validators=[MinValueValidator(1)]
    )
    amount = models.DecimalField(
        'Valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    due_date = models.DateField('Data de Vencimento')
    
    # Fatura de cartão (opcional)
    invoice = models.ForeignKey(
        'CreditCardInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installments',
        verbose_name='Fatura',
        help_text='Vincula esta parcela a uma fatura específica do cartão'
    )
    status = models.CharField(
        'Status',
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='installment',
        verbose_name='Transação Gerada',
        help_text='Transação criada automaticamente para esta parcela'
    )
    notes = models.TextField('Observações', blank=True, null=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['plan', 'installment_number']
        unique_together = [['plan', 'installment_number']]
        indexes = [
            models.Index(fields=['plan', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.plan.description} - Parcela {self.installment_number}/{self.plan.total_installments}"
    
    def clean(self):
        # Validar que o número da parcela não excede o total
        if self.plan and self.installment_number > self.plan.total_installments:
            raise ValidationError(
                f'Número da parcela não pode exceder {self.plan.total_installments}'
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CreditCard(models.Model):
    """
    Modelo para cartões de crédito.
    Permite controlar faturas, parcelamentos e transações vinculadas.
    """
    
    BRAND_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('elo', 'Elo'),
        ('amex', 'American Express'),
        ('hipercard', 'Hipercard'),
        ('other', 'Outro'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credit_cards',
        verbose_name='Usuário'
    )
    name = models.CharField(
        'Nome do Cartão',
        max_length=100,
        help_text='Ex: Nubank Platinum, Itaú Gold'
    )
    brand = models.CharField(
        'Bandeira',
        max_length=20,
        choices=BRAND_CHOICES
    )
    closing_day = models.PositiveIntegerField(
        'Dia de Fechamento',
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês em que a fatura fecha (1-31)'
    )
    due_day = models.PositiveIntegerField(
        'Dia de Vencimento',
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês em que a fatura vence (1-31)'
    )
    credit_limit = models.DecimalField(
        'Limite do Cartão',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Limite total do cartão (opcional)'
    )
    is_active = models.BooleanField('Ativo', default=True)
    notes = models.TextField('Observações', blank=True, null=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Cartão de Crédito'
        verbose_name_plural = 'Cartões de Crédito'
        ordering = ['-is_active', 'name']
        unique_together = [['user', 'name']]
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_brand_display()})"
    
    def clean(self):
        # Validar que o dia de vencimento é após o fechamento
        if self.due_day <= self.closing_day:
            raise ValidationError(
                'O dia de vencimento deve ser posterior ao dia de fechamento'
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CreditCardInvoice(models.Model):
    """
    Modelo para faturas de cartão de crédito.
    Permite controlar o valor total da fatura e comparar com gastos declarados.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('overdue', 'Atrasado'),
        ('partial', 'Parcialmente Pago'),
    ]
    
    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Cartão de Crédito'
    )
    reference_month = models.DateField(
        'Mês de Referência',
        help_text='Primeiro dia do mês de referência da fatura'
    )
    total_amount = models.DecimalField(
        'Valor Total da Fatura',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Valor total que consta na fatura do banco'
    )
    closing_date = models.DateField(
        'Data de Fechamento',
        help_text='Data em que a fatura fechou'
    )
    due_date = models.DateField(
        'Data de Vencimento',
        help_text='Data de vencimento da fatura'
    )
    status = models.CharField(
        'Status',
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_date = models.DateField(
        'Data do Pagamento',
        null=True,
        blank=True
    )
    paid_amount = models.DecimalField(
        'Valor Pago',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Valor já pago desta fatura'
    )
    notes = models.TextField('Observações', blank=True, null=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Fatura de Cartão'
        verbose_name_plural = 'Faturas de Cartão'
        ordering = ['-reference_month']
        unique_together = [['credit_card', 'reference_month']]
        indexes = [
            models.Index(fields=['credit_card', 'reference_month']),
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.credit_card.name} - {self.reference_month.strftime('%m/%Y')}"
    
    def clean(self):
        # Validar que paid_amount não excede total_amount
        if self.paid_amount > self.total_amount:
            raise ValidationError(
                'O valor pago não pode ser maior que o valor total da fatura'
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_declared_expenses(self):
        """
        Calcula o total de gastos declarados (transações + parcelas).
        """
        # Transações vinculadas a esta fatura
        transactions_total = self.transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Parcelas vinculadas a esta fatura
        installments_total = self.installments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return transactions_total + installments_total
    
    def get_unrelated_expenses(self):
        """
        Calcula despesas não relacionadas (valor da fatura - gastos declarados).
        """
        declared = self.get_declared_expenses()
        return self.total_amount - declared
    
    def get_remaining_balance(self):
        """
        Calcula o saldo restante a pagar.
        """
        return self.total_amount - self.paid_amount
