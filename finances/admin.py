from django.contrib import admin
from .models import (
    Category, Transaction, RecurringTemplate, 
    InstallmentPlan, Installment, CreditCard, CreditCardInvoice
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin para o modelo Category"""
    
    list_display = ['name', 'type', 'is_default', 'user', 'created_at']
    list_filter = ['type', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['type', 'name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'type', 'description')
        }),
        ('Configurações', {
            'fields': ('is_default', 'user')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Superusuário vê todas as categorias"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin para o modelo Transaction"""
    
    list_display = [
        'description', 'type', 'amount', 'category',
        'transaction_date', 'status', 'user', 'created_at'
    ]
    list_filter = [
        'type', 'status', 'is_recurring', 'recurrence',
        'transaction_date', 'created_at'
    ]
    search_fields = ['description', 'notes', 'category__name']
    ordering = ['-transaction_date', '-created_at']
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Superusuário vê todas as transações"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        """Associa a transação ao usuário logado se não tiver usuário"""
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecurringTemplate)
class RecurringTemplateAdmin(admin.ModelAdmin):
    """Admin para o modelo RecurringTemplate"""
    
    list_display = [
        'description', 'type', 'amount', 'day_of_month',
        'is_active', 'user', 'last_generated_date', 'created_at'
    ]
    list_filter = [
        'type', 'is_active', 'day_of_month', 'created_at'
    ]
    search_fields = ['description', 'notes', 'category__name']
    ordering = ['-is_active', 'day_of_month', 'description']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'category', 'type', 'description', 'amount')
        }),
        ('Configuração de Recorrência', {
            'fields': ('day_of_month', 'start_date', 'end_date', 'is_active')
        }),
        ('Controle', {
            'fields': ('last_generated_date', 'notes')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_generated_date']
    
    def get_queryset(self, request):
        """Superusuário vê todos os templates"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        """Associa o template ao usuário logado se não tiver usuário"""
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def activate_templates(self, request, queryset):
        """Ativa templates selecionados"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} template(s) ativado(s) com sucesso.')
    activate_templates.short_description = 'Ativar templates selecionados'
    
    def deactivate_templates(self, request, queryset):
        """Desativa templates selecionados"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} template(s) desativado(s) com sucesso.')
    deactivate_templates.short_description = 'Desativar templates selecionados'


class InstallmentInline(admin.TabularInline):
    """Inline para parcelas dentro do plano"""
    model = Installment
    extra = 0
    fields = ['installment_number', 'amount', 'due_date', 'status', 'transaction']
    readonly_fields = ['transaction']
    ordering = ['installment_number']


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    """Admin para o modelo InstallmentPlan"""
    
    list_display = [
        'description', 'type', 'total_installments', 'default_amount',
        'start_date', 'is_active', 'user', 'created_at'
    ]
    list_filter = [
        'type', 'is_active', 'created_at', 'start_date'
    ]
    search_fields = ['description', 'notes', 'category__name']
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    inlines = [InstallmentInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'category', 'type', 'description')
        }),
        ('Configuração do Plano', {
            'fields': ('total_installments', 'default_amount', 'start_date', 'is_active')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Superusuário vê todos os planos"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        """Associa o plano ao usuário logado se não tiver usuário"""
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_plans', 'deactivate_plans']
    
    def activate_plans(self, request, queryset):
        """Ativa planos selecionados"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} plano(s) ativado(s) com sucesso.')
    activate_plans.short_description = 'Ativar planos selecionados'
    
    def deactivate_plans(self, request, queryset):
        """Desativa planos selecionados"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} plano(s) desativado(s) com sucesso.')
    deactivate_plans.short_description = 'Desativar planos selecionados'


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    """Admin para o modelo Installment"""
    
    list_display = [
        'plan', 'installment_number', 'amount', 'due_date',
        'status', 'transaction', 'created_at'
    ]
    list_filter = [
        'status', 'due_date', 'created_at'
    ]
    search_fields = ['plan__description', 'notes']
    ordering = ['plan', 'installment_number']
    date_hierarchy = 'due_date'
       
    readonly_fields = ['created_at', 'updated_at', 'transaction']
    
    def get_queryset(self, request):
        """Superusuário vê todas as parcelas"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(plan__user=request.user)
    
    actions = ['mark_as_paid', 'mark_as_pending']
    
    def mark_as_paid(self, request, queryset):
        """Marca parcelas como pagas"""
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} parcela(s) marcada(s) como paga(s).')
    mark_as_paid.short_description = 'Marcar como pago'
    
    def mark_as_pending(self, request, queryset):
        """Marca parcelas como pendentes"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} parcela(s) marcada(s) como pendente(s).')
    mark_as_pending.short_description = 'Marcar como pendente'


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    """Admin para o modelo CreditCard"""
    
    list_display = [
        'name', 'brand', 'closing_day', 'due_day',
        'credit_limit', 'is_active', 'user', 'created_at'
    ]
    list_filter = [
        'brand', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'notes']
    ordering = ['-is_active', 'name']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'name', 'brand')
        }),
        ('Configuração de Fatura', {
            'fields': ('closing_day', 'due_day', 'credit_limit')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Superusuário vê todos os cartões"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        """Associa o cartão ao usuário logado se não tiver usuário"""
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_cards', 'deactivate_cards']
    
    def activate_cards(self, request, queryset):
        """Ativa cartões selecionados"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} cartão(ões) ativado(s) com sucesso.')
    activate_cards.short_description = 'Ativar cartões selecionados'
    
    def deactivate_cards(self, request, queryset):
        """Desativa cartões selecionados"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} cartão(ões) desativado(s) com sucesso.')
    deactivate_cards.short_description = 'Desativar cartões selecionados'


@admin.register(CreditCardInvoice)
class CreditCardInvoiceAdmin(admin.ModelAdmin):
    """Admin para o modelo CreditCardInvoice"""
    
    list_display = [
        'credit_card', 'reference_month_display', 'total_amount',
        'paid_amount', 'due_date', 'status', 'created_at'
    ]
    list_filter = [
        'status', 'reference_month', 'due_date', 'created_at'
    ]
    search_fields = ['credit_card__name', 'notes']
    ordering = ['-reference_month']
    date_hierarchy = 'reference_month'
    
    fieldsets = (
        ('Informações da Fatura', {
            'fields': ('credit_card', 'reference_month')
        }),
        ('Valores', {
            'fields': ('total_amount', 'paid_amount')
        }),
        ('Datas', {
            'fields': ('closing_date', 'due_date', 'payment_date')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def reference_month_display(self, obj):
        """Exibe o mês de referência formatado"""
        return obj.reference_month.strftime('%m/%Y')
    reference_month_display.short_description = 'Mês/Ano'
    
    def get_queryset(self, request):
        """Superusuário vê todas as faturas"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(credit_card__user=request.user)
    
    actions = ['mark_as_paid', 'mark_as_pending']
    
    def mark_as_paid(self, request, queryset):
        """Marca faturas como pagas"""
        from datetime import date
        updated = 0
        for invoice in queryset:
            invoice.status = 'paid'
            invoice.paid_amount = invoice.total_amount
            invoice.payment_date = date.today()
            invoice.save()
            updated += 1
        self.message_user(request, f'{updated} fatura(s) marcada(s) como paga(s).')
    mark_as_paid.short_description = 'Marcar como pago'
    
    def mark_as_pending(self, request, queryset):
        """Marca faturas como pendentes"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} fatura(s) marcada(s) como pendente(s).')
    mark_as_pending.short_description = 'Marcar como pendente'


# Customização do Admin Site
admin.site.site_header = 'MyDinDin - Administração'
admin.site.site_title = 'MyDinDin Admin'
admin.site.index_title = 'Painel de Controle Financeiro'
