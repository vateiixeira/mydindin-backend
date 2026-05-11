from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Transaction, RecurringTemplate, 
    InstallmentPlan, Installment, CreditCard, CreditCardInvoice
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer para o modelo User"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate_email(self, value):
        """Validar que o email é único"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Já existe um usuário com este email")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para o modelo Category"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    transactions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'type', 'type_display', 'description',
            'is_default', 'user', 'user_email', 'transactions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_default', 'user']
    
    def get_transactions_count(self, obj):
        """Retorna o número de transações associadas a esta categoria"""
        return obj.transactions.count()
    
    def validate(self, data):
        # Verificar se já existe uma categoria com o mesmo nome e tipo para o usuário
        request = self.context.get('request')
        if request and request.user:
            name = data.get('name')
            type_choice = data.get('type')
            user = data.get('user', request.user)
            
            # Excluir a própria instância da verificação (para updates)
            queryset = Category.objects.filter(name=name, type=type_choice, user=user)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    "Você já possui uma categoria com este nome e tipo"
                )
        
        return data


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Transaction"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    recurrence_display = serializers.CharField(source='get_recurrence_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    credit_card_name = serializers.CharField(source='credit_card.name', read_only=True, allow_null=True)
    invoice_reference = serializers.CharField(source='invoice.reference_month', read_only=True, allow_null=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_email', 'category', 'category_name',
            'type', 'type_display', 'description', 'amount',
            'transaction_date', 'due_date', 'payment_date',
            'is_recurring', 'recurrence', 'recurrence_display', 'recurrence_end_date',
            'status', 'status_display', 'notes',
            'payment_method', 'payment_method_display',
            'credit_card', 'credit_card_name', 'invoice', 'invoice_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def validate(self, data):
        # Validar que a categoria e a transação são do mesmo tipo
        category = data.get('category')
        transaction_type = data.get('type')
        
        if category and transaction_type and category.type != transaction_type:
            raise serializers.ValidationError(
                f"A categoria selecionada é do tipo '{category.get_type_display()}', "
                f"mas a transação é do tipo '{dict(Transaction.TYPE_CHOICES)[transaction_type]}'"
            )
        
        # Validar que se is_recurring é True, a recorrência não pode ser 'none'
        is_recurring = data.get('is_recurring', False)
        recurrence = data.get('recurrence', 'none')
        
        if is_recurring and recurrence == 'none':
            data['recurrence'] = 'monthly'
        
        if not is_recurring:
            data['recurrence'] = 'none'
            data['recurrence_end_date'] = None
        
        return data
    
    def validate_amount(self, value):
        """Validar que o valor é positivo"""
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero")
        return value


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de transações"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'category_name', 'type', 'type_display',
            'description', 'amount', 'transaction_date',
            'due_date', 'status', 'status_display'
        ]


class RecurringTemplateSerializer(serializers.ModelSerializer):
    """Serializer para templates de recorrência"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    credit_card_name = serializers.CharField(source='credit_card.name', read_only=True, allow_null=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True, allow_null=True)

    class Meta:
        model = RecurringTemplate
        fields = [
            'id', 'user', 'user_email', 'category', 'category_name',
            'type', 'type_display', 'description', 'amount',
            'day_of_month', 'is_active', 'start_date', 'end_date',
            'last_generated_date', 'notes',
            'payment_method', 'payment_method_display',
            'credit_card', 'credit_card_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_generated_date', 'created_at', 'updated_at', 'user']
    
    def validate(self, data):
        # Validar que a categoria e o template são do mesmo tipo
        category = data.get('category')
        template_type = data.get('type')
        
        if category and template_type and category.type != template_type:
            raise serializers.ValidationError(
                f"A categoria selecionada é do tipo '{category.get_type_display()}', "
                f"mas o template é do tipo '{dict(RecurringTemplate.TYPE_CHOICES)[template_type]}'"
            )
        
        # Validar que end_date é maior que start_date
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if end_date and start_date and end_date <= start_date:
            raise serializers.ValidationError(
                "A data de término deve ser posterior à data de início"
            )
        
        return data


class InstallmentSerializer(serializers.ModelSerializer):
    """Serializer para parcelas individuais"""
    
    plan_description = serializers.CharField(source='plan.description', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transaction_description = serializers.CharField(
        source='transaction.description',
        read_only=True,
        allow_null=True
    )
    invoice_reference = serializers.CharField(source='invoice.reference_month', read_only=True, allow_null=True)
    
    class Meta:
        model = Installment
        fields = [
            'id', 'plan', 'plan_description', 'installment_number',
            'amount', 'due_date', 'status', 'status_display',
            'transaction', 'transaction_description', 'invoice', 'invoice_reference',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validar que o número da parcela não excede o total
        plan = data.get('plan')
        installment_number = data.get('installment_number')
        
        if plan and installment_number and installment_number > plan.total_installments:
            raise serializers.ValidationError(
                f'Número da parcela não pode exceder {plan.total_installments}'
            )
        
        return data


class InstallmentPlanSerializer(serializers.ModelSerializer):
    """Serializer para planos de parcelamento"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    credit_card_name = serializers.CharField(source='credit_card.name', read_only=True, allow_null=True)
    installments_count = serializers.SerializerMethodField()
    paid_installments_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallmentPlan
        fields = [
            'id', 'user', 'user_email', 'category', 'category_name',
            'type', 'type_display', 'description', 'credit_card', 'credit_card_name',
            'total_installments', 'default_amount', 'start_date', 'is_active', 'notes',
            'installments_count', 'paid_installments_count', 'total_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_installments_count(self, obj):
        """Retorna o número total de parcelas criadas"""
        return obj.installments.count()
    
    def get_paid_installments_count(self, obj):
        """Retorna o número de parcelas pagas"""
        return obj.installments.filter(status='paid').count()
    
    def get_total_amount(self, obj):
        """Retorna o valor total de todas as parcelas"""
        return sum([inst.amount for inst in obj.installments.all()])
    
    def validate(self, data):
        # Validar que a categoria e o plano são do mesmo tipo
        category = data.get('category')
        plan_type = data.get('type')
        
        if category and plan_type and category.type != plan_type:
            raise serializers.ValidationError(
                f"A categoria selecionada é do tipo '{category.get_type_display()}', "
                f"mas o plano é do tipo '{dict(InstallmentPlan.TYPE_CHOICES)[plan_type]}'"
            )
        
        return data


class InstallmentPlanDetailSerializer(InstallmentPlanSerializer):
    """Serializer detalhado com lista de parcelas"""
    
    installments = InstallmentSerializer(many=True, read_only=True)
    
    class Meta(InstallmentPlanSerializer.Meta):
        fields = InstallmentPlanSerializer.Meta.fields + ['installments']


class CreditCardSerializer(serializers.ModelSerializer):
    """Serializer para cartões de crédito"""
    
    brand_display = serializers.CharField(source='get_brand_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    invoices_count = serializers.SerializerMethodField()
    active_invoices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditCard
        fields = [
            'id', 'user', 'user_email', 'name', 'brand', 'brand_display',
            'closing_day', 'due_day', 'credit_limit', 'is_active', 'notes',
            'invoices_count', 'active_invoices_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_invoices_count(self, obj):
        """Retorna o número total de faturas"""
        return obj.invoices.count()
    
    def get_active_invoices_count(self, obj):
        """Retorna o número de faturas pendentes ou atrasadas"""
        return obj.invoices.filter(status__in=['pending', 'overdue', 'partial']).count()
    
    def validate(self, data):
        # Validar que o dia de vencimento é após o fechamento
        closing_day = data.get('closing_day')
        due_day = data.get('due_day')
        
        if closing_day and due_day and due_day <= closing_day:
            raise serializers.ValidationError(
                'O dia de vencimento deve ser posterior ao dia de fechamento'
            )
        
        # Validar unicidade do nome do cartão para o usuário
        request = self.context.get('request')
        if request and request.user:
            name = data.get('name')
            user = data.get('user', request.user)
            
            queryset = CreditCard.objects.filter(name=name, user=user)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    "Você já possui um cartão com este nome"
                )
        
        return data


class CreditCardInvoiceSerializer(serializers.ModelSerializer):
    """Serializer para faturas de cartão"""
    
    credit_card_name = serializers.CharField(source='credit_card.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reference_month_display = serializers.SerializerMethodField()
    declared_expenses = serializers.SerializerMethodField()
    unrelated_expenses = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditCardInvoice
        fields = [
            'id', 'credit_card', 'credit_card_name', 'reference_month',
            'reference_month_display', 'total_amount', 'closing_date', 'due_date',
            'status', 'status_display', 'payment_date', 'paid_amount',
            'declared_expenses', 'unrelated_expenses', 'remaining_balance',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_reference_month_display(self, obj):
        """Retorna o mês de referência formatado"""
        return obj.reference_month.strftime('%m/%Y')
    
    def get_declared_expenses(self, obj):
        """Retorna gastos declarados (transações + parcelas)"""
        return float(obj.get_declared_expenses())
    
    def get_unrelated_expenses(self, obj):
        """Retorna despesas não relacionadas"""
        return float(obj.get_unrelated_expenses())
    
    def get_remaining_balance(self, obj):
        """Retorna saldo restante a pagar"""
        return float(obj.get_remaining_balance())
    
    def validate(self, data):
        # Validar que paid_amount não excede total_amount
        paid_amount = data.get('paid_amount', 0)
        total_amount = data.get('total_amount')
        
        if total_amount and paid_amount > total_amount:
            raise serializers.ValidationError(
                'O valor pago não pode ser maior que o valor total da fatura'
            )
        
        # Validar unicidade da fatura (cartão + mês de referência)
        credit_card = data.get('credit_card')
        reference_month = data.get('reference_month')
        
        if credit_card and reference_month:
            queryset = CreditCardInvoice.objects.filter(
                credit_card=credit_card,
                reference_month=reference_month
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Já existe uma fatura para este cartão no mês {reference_month.strftime('%m/%Y')}"
                )
        
        return data


class CreditCardInvoiceDetailSerializer(CreditCardInvoiceSerializer):
    """Serializer detalhado da fatura com transações e parcelas"""
    
    transactions = serializers.SerializerMethodField()
    installments = serializers.SerializerMethodField()
    
    class Meta(CreditCardInvoiceSerializer.Meta):
        fields = CreditCardInvoiceSerializer.Meta.fields + ['transactions', 'installments']
    
    def get_transactions(self, obj):
        """Retorna transações vinculadas a esta fatura"""
        from .serializers import TransactionListSerializer
        transactions = obj.transactions.all()
        return TransactionListSerializer(transactions, many=True).data
    
    def get_installments(self, obj):
        """Retorna parcelas vinculadas a esta fatura"""
        from .serializers import InstallmentSerializer
        installments = obj.installments.all()
        return InstallmentSerializer(installments, many=True).data

