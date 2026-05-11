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
        transactions, truncated = service.generate_months(self.template, 3)
        self.assertEqual(len(transactions), 3)
        self.assertFalse(truncated)
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
        transactions, truncated = service.generate_months(self.template, 2)
        self.assertEqual(len(transactions), 2)
        self.assertFalse(truncated)

    def test_generate_months_truncates_at_end_date(self):
        from finances.services.recurring_service import RecurringService
        from datetime import date
        service = RecurringService()
        # end_date no segundo mês futuro — pedindo 5 meses deve truncar
        from dateutil.relativedelta import relativedelta
        today = date.today()
        self.template.end_date = (today.replace(day=1) + relativedelta(months=1)).replace(day=28)
        self.template.save()
        transactions, truncated = service.generate_months(self.template, 5)
        self.assertTrue(truncated)
        self.assertLess(len(transactions), 5)
        for t in transactions:
            self.assertLessEqual(t.transaction_date, self.template.end_date)

    def test_generate_months_force_ignores_end_date(self):
        from finances.services.recurring_service import RecurringService
        from datetime import date
        from dateutil.relativedelta import relativedelta
        service = RecurringService()
        today = date.today()
        # end_date entre start_date e os meses a gerar — sem force truncaria
        self.template.end_date = today.replace(day=1) - relativedelta(days=1)
        if self.template.end_date <= self.template.start_date:
            self.template.end_date = self.template.start_date + relativedelta(days=1)
        self.template.save()
        # Força geração ignorando end_date
        transactions, truncated = service.generate_months(self.template, 2, force=True)
        self.assertEqual(len(transactions), 2)
        self.assertFalse(truncated)


class GenerateAllFromStartTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email='gafs@example.com',
            password='pass123',
            first_name='Gen',
            last_name='Test'
        )
        from finances.models import Category, RecurringTemplate
        from datetime import date
        self.cat = Category.objects.create(name='Salário GAFS', type='income', user=self.user)
        self.template = RecurringTemplate.objects.create(
            user=self.user,
            category=self.cat,
            type='income',
            description='Salário GAFS',
            amount='3000.00',
            day_of_month=10,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 4, 30),
        )

    def test_gera_todas_as_transacoes_no_intervalo(self):
        from finances.services.recurring_service import RecurringService
        from finances.models import Transaction
        txns = RecurringService().generate_all_from_start(self.template)
        # Jan, Fev, Mar, Abr (dia 10 em todos — dentro de end_date)
        self.assertEqual(len(txns), 4)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 4)

    def test_atualiza_last_generated_date(self):
        from finances.services.recurring_service import RecurringService
        from datetime import date
        RecurringService().generate_all_from_start(self.template)
        self.template.refresh_from_db()
        self.assertEqual(self.template.last_generated_date, date(2026, 4, 10))

    def test_exclui_transacao_apos_end_date(self):
        """day_of_month posterior ao último dia do mês final não gera transação extra."""
        from finances.models import Category, RecurringTemplate
        from finances.services.recurring_service import RecurringService
        from datetime import date
        # end_date = 30/abr, day_of_month = 10 → Abr/10 ok; Maio não é gerado
        txns = RecurringService().generate_all_from_start(self.template)
        datas = [t.transaction_date for t in txns]
        self.assertNotIn(date(2026, 5, 10), datas)

    def test_exclui_transacao_antes_de_start_date(self):
        """Quando day_of_month < start_date.day no primeiro mês, não gera antes de start_date."""
        from finances.models import Category, RecurringTemplate
        from finances.services.recurring_service import RecurringService
        from datetime import date
        # start_date = 20/jan, day_of_month = 5 → Jan/5 fica antes de start_date; não deve ser gerado
        self.template.start_date = date(2026, 1, 20)
        self.template.save()
        txns = RecurringService().generate_all_from_start(self.template)
        datas = [t.transaction_date for t in txns]
        self.assertNotIn(date(2026, 1, 5), datas)
        # Fev, Mar, Abr ainda são gerados
        self.assertIn(date(2026, 2, 10), datas)

    def test_respeita_limite_dias_do_mes(self):
        """day_of_month = 31 em fevereiro usa o último dia do mês."""
        from finances.models import Category, RecurringTemplate
        from finances.services.recurring_service import RecurringService
        from datetime import date
        self.template.day_of_month = 31
        self.template.end_date = date(2026, 2, 28)
        self.template.save()
        txns = RecurringService().generate_all_from_start(self.template)
        datas = [t.transaction_date for t in txns]
        self.assertIn(date(2026, 1, 31), datas)
        self.assertIn(date(2026, 2, 28), datas)

    def test_retorna_lista_vazia_sem_end_date(self):
        from finances.services.recurring_service import RecurringService
        self.template.end_date = None
        self.template.save()
        txns = RecurringService().generate_all_from_start(self.template)
        self.assertEqual(txns, [])


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
