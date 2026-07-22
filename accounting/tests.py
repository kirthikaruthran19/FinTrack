from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import TransactionForm, CategoryForm
from .models import Category, Transaction, Gst, Ledger


class TransactionViewTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Food"
        )

    def test_add_transaction_get(self):

        response = self.client.get(
            reverse("add_transaction")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "accounting/add_transaction.html"
        )

    def test_add_transaction_post(self):

        response = self.client.post(
            reverse("add_transaction"),
            {
                "date": timezone.now().date(),
                "description": "Restaurant",
                "amount": 1000,
                "type": "Expense",
                "category": self.category.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            Transaction.objects.count(),
            1
        )

        self.assertEqual(
            Gst.objects.count(),
            1
        )

        self.assertEqual(
            Ledger.objects.count(),
            1
        )


class GstReportTests(TestCase):

    def setUp(self):

        category = Category.objects.create(
            name="Travel"
        )

        transaction = Transaction.objects.create(
            date=timezone.now().date(),
            description="Taxi",
            amount=2000,
            type="Expense",
            category=category,
        )

        Gst.objects.create(
            transaction=transaction,
            gst_percentage=18,
        )

    def test_gst_report(self):

        response = self.client.get(
            reverse("gst_report")
        )

        self.assertEqual(
            response.status_code,
            200
        )


class TransactionFormTests(TestCase):

    def setUp(self):

        self.category = Category.objects.create(
            name="Salary"
        )

    def test_valid_transaction_form(self):

        form = TransactionForm(
            data={
                "date": timezone.now().date(),
                "description": "Monthly Salary",
                "amount": 50000,
                "type": "Income",
                "category": self.category.id,
            }
        )

        self.assertTrue(form.is_valid())

    def test_invalid_transaction_form(self):

        form = TransactionForm(
            data={}
        )

        self.assertFalse(form.is_valid())


class CategoryFormTests(TestCase):

    def test_valid_category(self):

        form = CategoryForm(
            data={
                "name": "Bills"
            }
        )

        self.assertTrue(form.is_valid())

    def test_invalid_category(self):

        form = CategoryForm(
            data={}
        )

        self.assertFalse(form.is_valid())


class ModelTests(TestCase):

    def test_category_model(self):

        category = Category.objects.create(
            name="Shopping"
        )

        self.assertEqual(
            str(category),
            "Shopping"
        )

    def test_transaction_model(self):

        category = Category.objects.create(
            name="Misc"
        )

        transaction = Transaction.objects.create(
            date=timezone.now().date(),
            description="Test",
            amount=Decimal("100.00"),
            type="Expense",
            category=category,
        )

        self.assertEqual(
            transaction.description,
            "Test"
        )

        self.assertEqual(
            transaction.amount,
            Decimal("100.00")
        )

        self.assertEqual(
            transaction.type,
            "Expense"
        )