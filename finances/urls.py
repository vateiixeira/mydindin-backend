from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    TransactionViewSet,
    RecurringTemplateViewSet,
    InstallmentPlanViewSet,
    InstallmentViewSet,
    CreditCardViewSet,
    CreditCardInvoiceViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'recurring-templates', RecurringTemplateViewSet, basename='recurring-template')
router.register(r'installment-plans', InstallmentPlanViewSet, basename='installment-plan')
router.register(r'installments', InstallmentViewSet, basename='installment')
router.register(r'credit-cards', CreditCardViewSet, basename='credit-card')
router.register(r'invoices', CreditCardInvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
]

