from django.test import TestCase


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
