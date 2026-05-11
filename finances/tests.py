from django.test import TestCase


class RecurringGenerateMonthsTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email='rectest@example.com',
            password='pass123',
            first_name='Rec',
            last_name='Test'
        )
        from finances.models import Category, RecurringTemplate
        from datetime import date
        self.cat = Category.objects.create(name='Salário', type='income', user=self.user)
        self.template = RecurringTemplate.objects.create(
            user=self.user,
            category=self.cat,
            type='income',
            description='Salário Mensal',
            amount='5000.00',
            day_of_month=5,
            start_date=date(2026, 1, 1)
        )

    def test_generate_months_creates_correct_count(self):
        from finances.services.recurring_service import RecurringService
        from finances.models import Transaction
        service = RecurringService()
        transactions = service.generate_months(self.template, 3)
        self.assertEqual(len(transactions), 3)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 3)

    def test_generate_months_updates_last_generated_date(self):
        from finances.services.recurring_service import RecurringService
        service = RecurringService()
        service.generate_months(self.template, 2)
        self.template.refresh_from_db()
        self.assertIsNotNone(self.template.last_generated_date)

    def test_generate_months_continues_from_last_generated(self):
        from finances.services.recurring_service import RecurringService
        service = RecurringService()
        # Primeira geração: 3 meses
        service.generate_months(self.template, 3)
        self.template.refresh_from_db()
        # Segunda geração: mais 2 meses, deve continuar de onde parou
        transactions = service.generate_months(self.template, 2)
        self.assertEqual(len(transactions), 2)


class MarkAllPaidTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass123',
            first_name='Test',
            last_name='User'
        )
        from finances.models import Category, InstallmentPlan
        self.cat = Category.objects.create(name='Teste', type='expense', user=self.user)
        from datetime import date
        self.plan = InstallmentPlan.objects.create(
            user=self.user,
            category=self.cat,
            type='expense',
            description='Plano Teste',
            total_installments=3,
            default_amount='100.00',
            start_date=date.today()
        )

    def test_mark_all_paid_marks_pending_and_overdue(self):
        from finances.models import Installment
        from datetime import date
        # Forçar uma parcela como overdue
        inst = self.plan.installments.first()
        inst.status = 'overdue'
        inst.save()

        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        resp = client.post(f'/api/installment-plans/{self.plan.id}/mark_all_paid/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('marked', resp.data)
        self.assertGreater(resp.data['marked'], 0)

        # Verificar que parcelas estão pagas
        for inst in self.plan.installments.all():
            self.assertEqual(inst.status, 'paid')
