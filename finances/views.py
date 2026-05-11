from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from .models import (
    Category, Transaction, RecurringTemplate, 
    InstallmentPlan, Installment, CreditCard, CreditCardInvoice
)
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    TransactionListSerializer,
    RecurringTemplateSerializer,
    InstallmentPlanSerializer,
    InstallmentPlanDetailSerializer,
    InstallmentSerializer,
    CreditCardSerializer,
    CreditCardInvoiceSerializer,
    CreditCardInvoiceDetailSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar categorias.
    Permite listar, criar, atualizar e deletar categorias.
    """
    
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'type', 'created_at']
    ordering = ['type', 'name']
    
    def get_queryset(self):
        """
        Retorna categorias padrão do sistema e categorias do usuário logado.
        """
        user = self.request.user
        return Category.objects.filter(
            Q(user=user) | Q(is_default=True, user__isnull=True)
        )
    
    def perform_create(self, serializer):
        """Associa a categoria ao usuário logado"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Endpoint customizado para listar categorias por tipo.
        Uso: /api/categories/by_type/?type=income ou ?type=expense
        """
        category_type = request.query_params.get('type', None)
        
        if not category_type:
            return Response(
                {'error': 'O parâmetro "type" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if category_type not in ['income', 'expense']:
            return Response(
                {'error': 'Tipo inválido. Use "income" ou "expense"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(type=category_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar transações financeiras.
    Permite listar, criar, atualizar e deletar transações.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'category', 'credit_card', 'invoice']
    search_fields = ['description', 'notes', 'category__name']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-transaction_date', '-created_at']
    
    def get_queryset(self):
        """
        Retorna apenas transações do usuário logado.
        Aceita filtros opcionais de período: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
        """
        queryset = Transaction.objects.filter(user=self.request.user).select_related('category', 'user')
        
        # Filtro opcional por período (start_date e end_date)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    transaction_date__gte=start,
                    transaction_date__lte=end
                )
            except ValueError:
                # Se a data for inválida, ignora o filtro
                pass
        elif start_date:
            # Apenas start_date fornecido
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(transaction_date__gte=start)
            except ValueError:
                pass
        elif end_date:
            # Apenas end_date fornecido
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(transaction_date__lte=end)
            except ValueError:
                pass
        
        return queryset
    
    def get_serializer_class(self):
        """Usa serializer resumido para listagem"""
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Associa a transação ao usuário logado"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_period(self, request):
        """
        Filtra transações por período.
        Uso: /api/transactions/by_period/?start_date=2024-01-01&end_date=2024-12-31
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Os parâmetros "start_date" e "end_date" são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            transaction_date__gte=start,
            transaction_date__lte=end
        )
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_month(self, request):
        """
        Filtra transações por mês.
        Uso: /api/transactions/by_month/?year=2024&month=10
        """
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not year or not month:
            return Response(
                {'error': 'Os parâmetros "year" e "month" são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            month = int(month)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'Valores inválidos para ano ou mês'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            transaction_date__year=year,
            transaction_date__month=month
        )
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Retorna um resumo financeiro do usuário.
        Opcionalmente filtra por período usando ?start_date e ?end_date
        """
        queryset = self.get_queryset()
        
        # Filtrar por período se fornecido
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    transaction_date__gte=start,
                    transaction_date__lte=end
                )
            except ValueError:
                return Response(
                    {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calcular totais
        incomes = queryset.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        expenses = queryset.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        balance = incomes - expenses
        
        # Contar transações
        total_transactions = queryset.count()
        pending_transactions = queryset.filter(status='pending').count()
        paid_transactions = queryset.filter(status='paid').count()
        overdue_transactions = queryset.filter(status='overdue').count()
        
        return Response({
            'total_incomes': float(incomes),
            'total_expenses': float(expenses),
            'balance': float(balance),
            'total_transactions': total_transactions,
            'pending_transactions': pending_transactions,
            'paid_transactions': paid_transactions,
            'overdue_transactions': overdue_transactions,
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Agrupa transações por categoria.
        Uso: /api/transactions/by_category/?type=expense ou ?type=income
        """
        transaction_type = request.query_params.get('type')
        
        if not transaction_type:
            return Response(
                {'error': 'O parâmetro "type" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if transaction_type not in ['income', 'expense']:
            return Response(
                {'error': 'Tipo inválido. Use "income" ou "expense"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar agregação do Django ORM para evitar duplicação
        categories_data = self.get_queryset().filter(
            type=transaction_type
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Formatar resposta
        result = [
            {
                'category': item['category__name'],
                'total': float(item['total'] or 0),
                'count': item['count']
            }
            for item in categories_data
        ]
        
        return Response(result)


class RecurringTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar templates de recorrência.
    Permite criar salários, aluguéis e outras transações recorrentes.
    """
    
    serializer_class = RecurringTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'notes']
    ordering_fields = ['day_of_month', 'amount', 'created_at']
    ordering = ['-is_active', 'day_of_month']
    
    def get_queryset(self):
        """Retorna apenas templates do usuário logado"""
        return RecurringTemplate.objects.filter(user=self.request.user).select_related('category', 'user')
    
    def perform_create(self, serializer):
        """Associa o template ao usuário logado e gera transações futuras se solicitado"""
        generate_now = self.request.data.get('generate_now', False)
        generate_months_count = int(self.request.data.get('generate_months', 3))
        with transaction.atomic():
            template = serializer.save(user=self.request.user)
            if generate_now:
                from .services.recurring_service import RecurringService
                service = RecurringService()
                if template.end_date:
                    service.generate_all_from_start(template)
                else:
                    service.generate_months(template, generate_months_count)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Pausa um template recorrente.
        Uso: POST /api/recurring-templates/{id}/pause/
        """
        template = self.get_object()
        template.is_active = False
        template.save()
        serializer = self.get_serializer(template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        Retoma um template recorrente pausado.
        Uso: POST /api/recurring-templates/{id}/resume/
        """
        template = self.get_object()
        template.is_active = True
        template.save()
        serializer = self.get_serializer(template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_now(self, request, pk=None):
        """
        Gera manualmente N meses de transações a partir do template.
        Uso: POST /api/recurring-templates/{id}/generate_now/
        Body: { "months": 3, "force": false }  (defaults: months=1, force=false)
        Quando force=True, ignora end_date do template.
        """
        template = self.get_object()

        months = request.data.get('months', 1)
        try:
            months = int(months)
            if months < 1 or months > 24:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'O campo "months" deve ser um número inteiro entre 1 e 24'},
                status=status.HTTP_400_BAD_REQUEST
            )

        force = bool(request.data.get('force', False))

        from .services.recurring_service import RecurringService
        service = RecurringService()
        transactions, truncated = service.generate_months(template, months, force=force)

        if transactions:
            template.refresh_from_db()
            response_data = {
                'generated': len(transactions),
                'truncated': truncated,
                'last_generated_date': template.last_generated_date.strftime('%m/%Y') if template.last_generated_date else None,
                'transaction_ids': [t.id for t in transactions]
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        elif truncated:
            return Response(
                {'generated': 0, 'truncated': True, 'error': 'Todas as datas solicitadas excedem o end_date do template'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {'error': 'Não foi possível gerar as transações'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Lista apenas templates ativos.
        Uso: GET /api/recurring-templates/active/
        """
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """
        Lista todas as transações geradas por este template.
        Uso: GET /api/recurring-templates/{id}/transactions/
        """
        template = self.get_object()
        transactions = Transaction.objects.filter(
            user=request.user,
            description=template.description,
            notes__contains=f"template: {template.description}"
        ).order_by('-transaction_date')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class InstallmentPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar planos de parcelamento.
    Permite criar consórcios, financiamentos e pagamentos parcelados.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'notes']
    ordering_fields = ['start_date', 'total_installments', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retorna apenas planos do usuário logado"""
        return InstallmentPlan.objects.filter(user=self.request.user).select_related('category', 'user')
    
    def get_serializer_class(self):
        """Usa serializer detalhado para retrieve"""
        if self.action == 'retrieve':
            return InstallmentPlanDetailSerializer
        return InstallmentPlanSerializer
    
    def perform_create(self, serializer):
        """Associa o plano ao usuário logado"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def installments(self, request, pk=None):
        """
        Lista todas as parcelas de um plano.
        Uso: GET /api/installment-plans/{id}/installments/
        """
        plan = self.get_object()
        installments = plan.installments.all()
        serializer = InstallmentSerializer(installments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pending_installments(self, request, pk=None):
        """
        Lista parcelas pendentes de um plano.
        Uso: GET /api/installment-plans/{id}/pending_installments/
        """
        plan = self.get_object()
        installments = plan.installments.filter(status='pending')
        serializer = InstallmentSerializer(installments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Retorna um resumo do plano de parcelamento.
        Uso: GET /api/installment-plans/{id}/summary/
        """
        plan = self.get_object()
        installments = plan.installments.all()
        
        total = installments.count()
        pending = installments.filter(status='pending').count()
        paid = installments.filter(status='paid').count()
        overdue = installments.filter(status='overdue').count()
        generated = installments.filter(status='generated').count()
        
        total_amount = sum([inst.amount for inst in installments])
        paid_amount = sum([inst.amount for inst in installments.filter(status='paid')])
        pending_amount = total_amount - paid_amount
        
        return Response({
            'plan_id': plan.id,
            'description': plan.description,
            'total_installments': total,
            'pending_installments': pending,
            'paid_installments': paid,
            'overdue_installments': overdue,
            'generated_installments': generated,
            'total_amount': float(total_amount),
            'paid_amount': float(paid_amount),
            'pending_amount': float(pending_amount),
            'progress_percentage': round((paid / total * 100), 2) if total > 0 else 0
        })

    @action(detail=True, methods=['post'])
    def mark_all_paid(self, request, pk=None):
        """
        Marca todas as parcelas não pagas de um plano como pagas.
        Uso: POST /api/installment-plans/{id}/mark_all_paid/
        """
        from django.db import transaction as db_transaction
        plan = self.get_object()
        installments = plan.installments.filter(status__in=['pending', 'overdue', 'generated'])
        count = 0
        with db_transaction.atomic():
            for installment in installments:
                if installment.transaction:
                    installment.transaction.status = 'paid'
                    installment.transaction.payment_date = date.today()
                    installment.transaction.save()
                installment.status = 'paid'
                installment.save()
                count += 1
        return Response({'marked': count})


class InstallmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar parcelas individuais.
    Permite visualizar e editar parcelas de planos.
    """
    
    serializer_class = InstallmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['due_date', 'installment_number', 'amount']
    ordering = ['due_date', 'installment_number']
    
    def get_queryset(self):
        """Retorna apenas parcelas dos planos do usuário logado"""
        return Installment.objects.filter(
            plan__user=self.request.user
        ).select_related('plan', 'transaction')
    
    def perform_update(self, serializer):
        """
        Atualiza a parcela e sincroniza o valor da transação vinculada.
        Se o amount da parcela for alterado e existir uma transação vinculada,
        atualiza também o amount da transação.
        """
        installment = self.get_object()
        old_amount = installment.amount
        
        # Salva a parcela com os novos dados
        updated_installment = serializer.save()
        
        # Se o amount mudou e existe uma transação vinculada, atualiza a transação
        if 'amount' in serializer.validated_data:
            new_amount = serializer.validated_data['amount']
            
            if new_amount != old_amount and updated_installment.transaction:
                transaction = updated_installment.transaction
                transaction.amount = new_amount
                transaction.save()
                
                # Se a parcela está vinculada a uma fatura, recalcula o total
                if updated_installment.invoice:
                    from .services.invoice_service import InvoiceService
                    InvoiceService.update_invoice_total(updated_installment.invoice)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Lista parcelas com vencimento próximo (próximos 30 dias).
        Uso: GET /api/installments/upcoming/?days=30
        """
        from datetime import timedelta
        
        days = int(request.query_params.get('days', 30))
        today = date.today()
        future_date = today + timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            due_date__gte=today,
            due_date__lte=future_date,
            status__in=['pending', 'generated']
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Lista parcelas atrasadas.
        Uso: GET /api/installments/overdue/
        """
        queryset = self.get_queryset().filter(status='overdue')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        Marca uma parcela como paga.
        Uso: POST /api/installments/{id}/mark_paid/
        """
        installment = self.get_object()
        
        # Se já existe uma transação, marca ela como paga
        if installment.transaction:
            installment.transaction.status = 'paid'
            installment.transaction.payment_date = date.today()
            installment.transaction.save()
        
        installment.status = 'paid'
        installment.save()
        
        serializer = self.get_serializer(installment)
        return Response(serializer.data)


class CreditCardViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar cartões de crédito.
    Permite listar, criar, atualizar e deletar cartões.
    """
    
    serializer_class = CreditCardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand', 'notes']
    ordering_fields = ['name', 'created_at', 'due_day', 'closing_day']
    ordering = ['-is_active', 'name']
    
    def get_queryset(self):
        """Retorna apenas cartões do usuário logado"""
        return CreditCard.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associa o cartão ao usuário logado"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Lista apenas cartões ativos.
        Uso: GET /api/credit-cards/active/
        """
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desativa um cartão.
        Uso: POST /api/credit-cards/{id}/deactivate/
        """
        card = self.get_object()
        card.is_active = False
        card.save()
        serializer = self.get_serializer(card)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativa um cartão.
        Uso: POST /api/credit-cards/{id}/activate/
        """
        card = self.get_object()
        card.is_active = True
        card.save()
        serializer = self.get_serializer(card)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """
        Lista todas as faturas de um cartão.
        Uso: GET /api/credit-cards/{id}/invoices/
        """
        card = self.get_object()
        invoices = card.invoices.all()
        serializer = CreditCardInvoiceSerializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_invoices(self, request, pk=None):
        """
        Gera faturas faltantes para o cartão desde o mês mais antigo relevante até o mês atual.
        Uso: POST /api/credit-cards/{id}/generate_invoices/
        """
        card = self.get_object()

        from django.db import transaction
        from .services.invoice_service import InvoiceService
        with transaction.atomic():
            result = InvoiceService.generate_invoices_for_card(card)

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Retorna um resumo do cartão.
        Uso: GET /api/credit-cards/{id}/summary/
        """
        card = self.get_object()

        total_invoices = card.invoices.count()
        pending_invoices = card.invoices.filter(status='pending').count()
        paid_invoices = card.invoices.filter(status='paid').count()
        overdue_invoices = card.invoices.filter(status='overdue').count()
        
        total_transactions = card.transactions.count()
        total_installment_plans = card.installment_plans.count()
        
        return Response({
            'card_id': card.id,
            'card_name': card.name,
            'brand': card.get_brand_display(),
            'is_active': card.is_active,
            'credit_limit': float(card.credit_limit) if card.credit_limit else None,
            'total_invoices': total_invoices,
            'pending_invoices': pending_invoices,
            'paid_invoices': paid_invoices,
            'overdue_invoices': overdue_invoices,
            'total_transactions': total_transactions,
            'total_installment_plans': total_installment_plans,
        })


class CreditCardInvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar faturas de cartão de crédito.
    Permite listar, criar, atualizar e deletar faturas.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['credit_card__name', 'notes']
    ordering_fields = ['reference_month', 'due_date', 'total_amount', 'created_at']
    ordering = ['-reference_month']
    
    def get_queryset(self):
        """Retorna apenas faturas dos cartões do usuário logado"""
        return CreditCardInvoice.objects.filter(
            credit_card__user=self.request.user
        ).select_related('credit_card')
    
    def get_serializer_class(self):
        """Usa serializer detalhado para retrieve"""
        if self.action == 'retrieve':
            return CreditCardInvoiceDetailSerializer
        return CreditCardInvoiceSerializer
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Lista faturas pendentes.
        Uso: GET /api/invoices/pending/
        """
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Lista faturas atrasadas.
        Uso: GET /api/invoices/overdue/
        """
        queryset = self.get_queryset().filter(status='overdue')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Retorna resumo detalhado da fatura (como na imagem).
        Uso: GET /api/invoices/{id}/summary/
        """
        invoice = self.get_object()
        
        # Calcular gastos
        declared_expenses = invoice.get_declared_expenses()
        unrelated_expenses = invoice.get_unrelated_expenses()
        remaining_balance = invoice.get_remaining_balance()
        
        # Contar itens
        transactions = invoice.transactions.all()
        installments = invoice.installments.all()
        
        # Preparar lista de detalhes
        details = []
        
        # Adicionar transações
        for transaction in transactions:
            details.append({
                'type': 'transaction',
                'id': transaction.id,
                'name': transaction.description,
                'category': transaction.category.name,
                'amount': float(transaction.amount)
            })
                
        return Response({
            'invoice_id': invoice.id,
            'credit_card': invoice.credit_card.name,
            'reference_month': invoice.reference_month.strftime('%m/%Y'),
            'closing_date': invoice.closing_date,
            'due_date': invoice.due_date,
            'status': invoice.status,
            'total_amount': float(invoice.total_amount),
            'declared_expenses': float(declared_expenses),
            'unrelated_expenses': float(unrelated_expenses),
            'paid_amount': float(invoice.paid_amount),
            'remaining_balance': float(remaining_balance),
            'transactions_count': transactions.count(),
            'installments_count': installments.count(),
            'details': details
        })
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        Marca uma fatura como paga.
        Uso: POST /api/invoices/{id}/mark_paid/
        Payload opcional: {"amount": 5000.00}
        """
        invoice = self.get_object()
        
        # Pegar o valor pago do payload (ou usar o total)
        amount = request.data.get('amount', invoice.total_amount)
        
        invoice.paid_amount = amount
        invoice.payment_date = date.today()
        
        # Atualizar status
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = 'paid'
        elif invoice.paid_amount > 0:
            invoice.status = 'partial'
        
        invoice.save()
        
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_transaction(self, request, pk=None):
        """
        Adiciona uma transação à fatura.
        Uso: POST /api/invoices/{id}/add_transaction/
        Payload: {
            "category": 1,
            "description": "Supermercado",
            "amount": 1000.00,
            "transaction_date": "2024-10-15"
        }
        """
        invoice = self.get_object()
        
        # Criar a transação vinculada à fatura e ao cartão
        data = request.data.copy()
        data['type'] = 'expense'
        data['credit_card'] = invoice.credit_card.id
        data['invoice'] = invoice.id
        
        serializer = TransactionSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def link_installment(self, request, pk=None):
        """
        Vincula uma parcela existente à fatura.
        Uso: POST /api/invoices/{id}/link_installment/
        Payload: {"installment_id": 123}
        """
        invoice = self.get_object()
        installment_id = request.data.get('installment_id')

        if not installment_id:
            return Response(
                {'error': 'O campo installment_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            installment = Installment.objects.get(
                id=installment_id,
                plan__user=request.user
            )

            # Vincular à fatura
            installment.invoice = invoice
            installment.save()

            return Response({
                'message': 'Parcela vinculada à fatura com sucesso',
                'installment': InstallmentSerializer(installment).data
            })

        except Installment.DoesNotExist:
            return Response(
                {'error': 'Parcela não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def create_payment_transaction(self, request, pk=None):
        """
        Cria ou atualiza a transação de pagamento da fatura.
        Uso: POST /api/invoices/{id}/create_payment_transaction/
        Payload opcional: {"payment_date": "2026-05-10", "amount": "1234.56"}
        """
        from .services.invoice_service import InvoiceService
        from datetime import datetime
        from decimal import Decimal, InvalidOperation

        invoice = self.get_object()

        payment_date = None
        raw_date = request.data.get('payment_date')
        if raw_date:
            try:
                payment_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de data inválido. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        amount = None
        raw_amount = request.data.get('amount')
        if raw_amount is not None:
            try:
                amount = Decimal(str(raw_amount))
                if amount <= 0:
                    raise ValueError
            except (ValueError, InvalidOperation):
                return Response(
                    {'error': 'Valor inválido. Informe um número positivo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        txn = InvoiceService.create_payment_transaction(invoice, payment_date=payment_date, amount=amount)
        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def remove_payment_transaction(self, request, pk=None):
        """
        Remove a transação de pagamento da fatura.
        Uso: DELETE /api/invoices/{id}/remove_payment_transaction/
        """
        from .services.invoice_service import InvoiceService

        invoice = self.get_object()

        if not invoice.payment_transaction_id:
            return Response(
                {'error': 'Esta fatura não possui transação de pagamento.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        InvoiceService.remove_payment_transaction(invoice)
        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)
